"""
Main module for handling and instantiating synaptical connections and gap-junctions
"""
from __future__ import absolute_import
import hashlib
import logging
import numpy
from collections import defaultdict
from itertools import chain
from os import path as ospath

from .core import NeurodamusCore as Nd
from .core import ProgressBarRank0 as ProgressBar, MPI
from .core import run_only_rank0
from .core.configuration import GlobalConfig, SimConfig, ConfigurationError
from .connection import Connection, ReplayMode
from .io.cell_readers import TargetSpec
from .io.synapse_reader import SynapseReader
from .utils import compat, bin_search, dict_filter_map
from .utils.logging import log_verbose, log_all
from .utils.timeit import timeit


class ConnectionSet(object):
    """
    A dataset of connections.
    Several populations may exist with different seeds
    """

    def __init__(self, src_id, dst_id, conn_factory=Connection):
        # Connections indexed by post-gid, then ordered by pre-gid
        self.src_id = src_id
        self.dst_id = dst_id
        self.src_name = None
        self.dst_name = None
        self.virtual_source = False
        self._conn_factory = conn_factory
        self._connections_map = defaultdict(list)
        self._conn_count = 0

    def __contains__(self, item):
        return item in self._connections_map

    def __getitem__(self, item):
        return self._connections_map[item]

    def get(self, item):
        return self._connections_map.get(item)

    def items(self):
        """Iterate over the population as tuples (dst_gid, [connections])"""
        return self._connections_map.items()

    def target_gids(self):
        """Get the list of all targets gids in this Population"""
        return self._connections_map.keys()

    def all_connections(self):
        """Get an iterator over all the connections."""
        return chain.from_iterable(self._connections_map.values())

    def _find_connection(self, sgid, tgid, exact=True):
        """Finds a connection, given its source and destination gids.

        Returns:
            tuple: connection list and index.
                If the element doesnt exist, index depends on 'exact':
                None if exact=True, otherwise the insertion index.
        """
        cell_conns = self._connections_map[tgid]
        pos = 0
        if cell_conns:
            pos = bin_search(cell_conns, sgid, lambda x: x.sgid)
        if exact and (pos == len(cell_conns) or cell_conns[pos].sgid != sgid):
            # Not found
            return cell_conns, None
        return cell_conns, pos

    # -
    def get_connection(self, sgid, tgid):
        """Retrieves a connection from the pre and post gids.

        Returns:
            Connection: A connection object if it exists. None otherwise
        """
        conn_lst, idx = self._find_connection(sgid, tgid)
        return None if idx is None else conn_lst[idx]

    # -
    def store_connection(self, conn):
        """When we have created a new connection (sgid->tgid), store it
        in order in our structure for faster retrieval later

        Args:
            conn: The connection object to be stored
        """
        cell_conns, pos = self._find_connection(conn.sgid, conn.tgid, exact=False)
        if cell_conns and pos < len(cell_conns) and cell_conns[pos].sgid == conn.sgid:
            logging.error("Attempt to store existing connection: %d->%d",
                          conn.sgid, conn.tgid)
            return
        self._conn_count += 1
        cell_conns.insert(pos, conn)

    # -
    def get_or_create_connection(self, sgid, tgid, **kwargs):
        """Returns a connection by pre-post gid, creating if required."""
        conns = self._connections_map[tgid]
        pos = 0
        if conns:
            # optimize for ordered insertion, and handle when sgid is not used
            last_conn = conns[-1]
            if last_conn.sgid in (sgid, None):
                return last_conn
            if last_conn.sgid < sgid:
                pos = len(conns)
            else:
                pos = bin_search(conns, sgid, lambda x: x.sgid)
                if conns[pos].sgid == sgid:
                    return conns[pos]
        # Not found. Create & insert
        cur_conn = self._conn_factory(sgid, tgid, self.src_id, self.dst_id, **kwargs)
        conns.insert(pos, cur_conn)
        self._conn_count += 1
        return cur_conn

    # -
    def get_connections(self, post_gids, pre_gids=None):
        """Get all connections between groups of gids."""
        if isinstance(post_gids, int):
            if pre_gids is None:
                return self._connections_map[post_gids]
            elif isinstance(pre_gids, int):
                elem = self.get_connection(pre_gids, post_gids)
                return (elem,) if elem is not None else ()

        post_gid_conn_lists = (
            self._connections_map.values() if post_gids is None
            else (self._connections_map[post_gids],) if isinstance(post_gids, int)
            else (self._connections_map[tgid] for tgid in post_gids)
        )
        if pre_gids is None:
            return chain.from_iterable(post_gid_conn_lists)
        elif isinstance(pre_gids, int):
            # Return a generator which is employing bin search
            return (conns[posi] for conns in post_gid_conn_lists
                    for posi in (bin_search(conns, pre_gids, lambda x: x.sgid),)
                    if posi < len(conns) and conns[posi].sgid == pre_gids)
        else:
            # Generic case. Looks through all conns in selected tgids
            pre_gids = set(pre_gids)
            return (c for conns in post_gid_conn_lists
                    for c in conns
                    if c.sgid in pre_gids)

    def get_synapse_params_gid(self, target_gid):
        """Get an iterator over all the synapse parameters of a target
        cell connections.
        """
        conns = self._connections_map[target_gid]
        return chain.from_iterable(c.synapse_params for c in conns)

    def delete(self, sgid, tgid):
        """Removes a given connection from the population."""
        conn_lst, idx = self._find_connection(sgid, tgid)
        if idx is None:
            logging.error("Non-existing connection to delete: %d->%d", sgid, tgid)
            return
        self._conn_count -= 1
        del conn_lst[idx]

    def delete_group(self, post_gids, pre_gids=None):
        """Removes a set of connections from the population."""
        for conns, indices in self._find_connections(post_gids, pre_gids):
            conns[:] = numpy.delete(conns, indices, axis=0).tolist()
            self._conn_count -= len(indices)

    def count(self):
        return self._conn_count

    # -
    def _find_connections(self, post_gids, pre_gids=None):
        """Get the indices of the connections between groups of gids"""
        post_gid_conn_lists = (
            self._connections_map.values() if post_gids is None
            else (self._connections_map[post_gids],) if isinstance(post_gids, int)
            else (self._connections_map[tgid] for tgid in post_gids)
        )

        if pre_gids is None:
            return ((conns, range(len(conns))) for conns in post_gid_conn_lists)

        sgids_interest = [pre_gids] if isinstance(pre_gids, int) else pre_gids
        return (
            (conns, numpy.searchsorted(
                numpy.fromiter((c.sgid for c in conns), dtype="int64", count=len(conns)),
                sgids_interest))
            for conns in post_gid_conn_lists
        )

    def ids_match(self, population_ids, dst_second=None):
        """Whereas a given population_id selector matches population
        """
        if isinstance(population_ids, tuple):
            expr_src, expr_dst = population_ids
        else:
            expr_src, expr_dst = (population_ids, dst_second)
        return ((expr_src is None or expr_src == self.src_id) and
                (expr_dst is None or expr_dst == self.dst_id))

    def is_default(self):
        return self.src_id == 0 and self.dst_id == 0

    def __str__(self):
        if self.is_default():
            return "<ConnectionSet: Default>"
        return "<ConnectionSet: %d-%d (%s->%s)>" % (
               self.src_id, self.dst_id, self.src_name, self.dst_name)

    def __repr__(self):
        return str(self)


class ConnectionManagerBase(object):
    """
    An abstract base class common to Synapse and GapJunction connections

    Connection Managers hold and manage connectivity among cell populations.
    For every src-dst pop pairs a new ConnectionManahger is created. The only case
    it holds several ConnectionSets is for old-style projections (no population names)
   """

    CONNECTIONS_TYPE = None
    """The type of connections subclasses handle"""

    # Set depending Classes, customizable
    ConnectionSet = ConnectionSet
    SynapseReader = SynapseReader
    conn_factory = Connection

    cell_manager = property(lambda self: self._cell_manager)
    src_cell_manager = property(lambda self: self._src_cell_manager)
    is_file_open = property(lambda self: bool(self._synapse_reader))
    src_pop_offset = property(lambda self: self._src_cell_manager.local_nodes.offset)
    target_pop_offset = property(lambda self: self._cell_manager.local_nodes.offset)

    # -
    def __init__(self, circuit_conf, target_manager, cell_manager, src_cell_manager=None, **kw):
        """Base class c-tor for connections (Synapses & Gap-Junctions)

        Args:
            circuit_conf: A circuit config object where to get the synapse source from
                or None if the ConnecionManager is to be constructed empty
            target_manager: A target manager, where to query target cells
            cell_manager: Manager to query the local target cells
            src_cell_manager: Manager to query the local source cells [default: None -> internal]
            load_offsets: Whether to load synapse offsets

        """
        self._target_manager = target_manager
        self._cell_manager = cell_manager
        self._src_cell_manager = src_cell_manager or cell_manager

        self._populations = {}  # Multiple edge populations support. key is a tuple (src, dst)
        self._cur_population = None
        self._disabled_conns = defaultdict(list)

        self._synapse_reader = None
        self._raw_gids = cell_manager.local_nodes.raw_gids()
        self._total_connections = 0
        self.circuit_conf = circuit_conf
        self._load_offsets = False
        self._src_target_filter = None  # filter by src target in all_connect (E.g: GapJ)

    def __str__(self):
        return "<{:s} | {:s} -> {:s}>".format(
            self.__class__.__name__, str(self._src_cell_manager), str(self._cell_manager))

    def open_edge_location(self, syn_source, circuit_conf, **kw):
        edge_file, *pop = syn_source.split(":")
        pop_name = pop[0] if pop else None
        n_files = circuit_conf.get("NumSynapseFiles")
        src_pop_id = _get_projection_population_id(circuit_conf)
        return self.open_synapse_file(edge_file, pop_name, n_files, src_pop_id=src_pop_id, **kw)

    def open_synapse_file(self, synapse_file, edge_population, n_files=1, load_offsets=False, *,
                          src_pop_id=None, src_name=None, **_kw):
        """Initializes a reader for Synapses config objects and associated population

        Args:
            synapse_file: The nrn/edge file. For old nrn files it may be a dir.
            edge_population: The population of the edges
            n_files: (nrn only) the number of nrn files in the directory (without nrn.h5)
            load_offsets: Whether the synapse offset should be loaded. So far only for NGV
            src_pop_id: (compat) Allow overriding the src population ID
            src_name: The source pop name, normally matching that of the source cell manager
        """
        if not ospath.exists(synapse_file):
            raise ConfigurationError("Connectivity (Edge) file not found: {}".format(synapse_file))
        if ospath.isdir(synapse_file):
            logging.warning("Edges source is a directory (legacy nrn.h5 only)")
            if ospath.isfile(ospath.join(synapse_file, "nrn.h5")):
                n_files = 1

        self._synapse_reader = self._open_synapse_file(synapse_file, edge_population, n_files)
        self._load_offsets = load_offsets
        if load_offsets:
            if not self._synapse_reader.has_property("synapse_index"):
                raise Exception("Synapse offsets required but not available. "
                                "Please use a more recent version of neurodamus-core/synapse-tool")

        self._init_conn_population(src_name, src_pop_id)
        self._unlock_all_connections()  # Allow appending synapses from new sources
        return synapse_file

    # - override if needed
    def _open_synapse_file(self, synapse_file, pop_name, n_nrn_files=None):
        logging.info("Opening Synapse file %s, population: %s", synapse_file, pop_name)
        return self.SynapseReader.create(
            synapse_file, self.CONNECTIONS_TYPE, pop_name,
            n_nrn_files, self._raw_gids,  # Used eventually by NRN reader
            extracellular_calcium=SimConfig.extracellular_calcium
        )

    def _init_conn_population(self, src_pop_name, pop_id_override):
        if not src_pop_name:
            src_pop_name = self._src_cell_manager.population_name
        dst_pop_name = self._cell_manager.population_name
        src_pop_id, dst_pop_id = self._compute_pop_ids(src_pop_name, dst_pop_name, pop_id_override)

        if self._cur_population and src_pop_id == 0 and not src_pop_name:
            logging.warning("Neither Sonata population nor populationID set. "
                            "Edges will be merged with base circuit")

        cur_pop = self.select_connection_set(src_pop_id, dst_pop_id)  # type: ConnectionSet
        cur_pop.src_name = src_pop_name
        cur_pop.dst_name = dst_pop_name
        cur_pop.virtual_source = (self._src_cell_manager.is_virtual
                                  or src_pop_name != self._src_cell_manager.population_name
                                  or pop_id_override and not src_pop_name)
        logging.info("Loading connections to population: %s", cur_pop)

    def _compute_pop_ids(self, src_pop, dst_pop, src_pop_id=None):
        """Compute pop id automatically. pop src 0 is base population.
        if src_pop_id is provided, it will be used instead.
        """
        def make_id(node_pop):
            pop_hash = hashlib.md5(node_pop.encode()).digest()
            return ((pop_hash[1] & 0x0f) << 8) + pop_hash[0]  # id: 12bit hash

        dst_pop_id = 0 if self._cell_manager.is_default else make_id(dst_pop)
        if src_pop_id is None:
            src_pop_id = 0 if self._src_cell_manager.is_default else make_id(src_pop)
        return src_pop_id, dst_pop_id

    # -
    def select_connection_set(self, src_pop_id, dst_pop_id):
        """Select the active population of connections given src and dst node pop ids.
        `connect_all()` and `connect_group()` will apply only to the active population.

        Returns: The selected ConnectionSet, eventually created
        """
        self._cur_population = self.get_population(src_pop_id, dst_pop_id)
        return self._cur_population

    # -
    def get_population(self, src_pop_id, dst_pop_id=0):
        """Retrieves a connection set given node src and dst pop ids"""
        pop = self._populations.get((src_pop_id, dst_pop_id))
        if not pop:
            pop = self.ConnectionSet(src_pop_id, dst_pop_id, conn_factory=self.conn_factory)
            self._populations[(src_pop_id, dst_pop_id)] = pop
        return pop

    # NOTE: Several methods use a selector of the connectivity populations
    # which, to be backwards compat, can be a single ID of the src_population
    # or a tuple to specify source and destination

    def find_populations(self, population_ids):
        """Finds the populations that match a given population selector.

        Args:
            population_ids: A population ids selector. Accepted formats:

                - None: All
                - int: selects matching source population id.
                - tuple(src: Any, dst: Any): Specify source and dest.
                  Each value can also be None, e.g.: (None, 1) selects all
                  populations having post id 1
        """
        if (isinstance(population_ids, tuple)
                and population_ids[0] is not None
                and population_ids[1] is not None):
            return [self._populations[population_ids]]
        return [
            pop for pop in self._populations.values()
            if pop.ids_match(population_ids)
        ]

    # -
    def all_connections(self):
        """Retrieves all the existing connections"""
        return chain.from_iterable(
            pop.all_connections() for pop in self._populations.values())

    @property
    def connection_count(self):
        return self._total_connections

    @property
    def current_population(self):
        return self._cur_population

    # -
    def get_connections(self, post_gids, pre_gids=None, population_ids=None):
        """Retrieves all connections that match post and pre gids eventually
        in a subset of the populations.

        Note: Due to multi-population, a connection may not be unique
        for a given pre-post gid pair. As such get_connection() doesn't
        make sense anymore and this method shall be used instead.

        Args:
            post_gids: The target gids of the connections to search (None = All)
            pre_gids: idem for pre-gids. [Default: all)
            population_ids: A int/tuple of populations ids. Default: all

        """
        for pop in self.find_populations(population_ids):
            for conn in pop.get_connections(post_gids, pre_gids):
                yield conn

    # -
    def create_connections(self, src_target=None, dst_target=None):
        """Creates connections according to loaded parameters in 'Connection'
        blocks of the BlueConfig in the currently active ConnectionSet.

        If no Connection block relates to the current population, then load all
        edges. If a single blocks exists with Weight=0, skip creation entirely.

        Args:
            src_target: Target name to restrict creating connections coming from it
            dst_target: Target name to restrict creating connections going into it
        """
        conn_src_pop = self.current_population.src_name
        conn_dst_pop = self.current_population.dst_name
        matching_conns = [
            conn for conn in SimConfig.connections.values()
            if TargetSpec(conn.get("Source")).match_filter(conn_src_pop, src_target)
            and TargetSpec(conn.get("Destination")).match_filter(conn_dst_pop, dst_target)
        ]

        if not matching_conns:
            logging.info("No matching Connection blocks. Loading all synapses...")
            self.connect_all()
            return

        # if we have a single connect block with weight=0, skip synapse creation entirely
        if len(matching_conns) == 1 and matching_conns[0].get("Weight") == .0:
            logging.warning("SKIPPING Connection create since they have invariably weight=0")
            return

        logging.info("Creating group connections (%d groups match)", len(matching_conns))
        for conn_conf in matching_conns:
            if "Delay" in conn_conf:
                # Delayed connections are for configuration only, not creation
                continue

            # check if we are not supposed to create (only configure later)
            if conn_conf.get("CreateMode") == "NoCreate":
                continue

            conn_src = conn_conf["Source"]
            conn_dst = conn_conf["Destination"]
            synapse_id = conn_conf.get("SynapseID")
            mod_override = None
            if "ModOverride" in conn_conf:
                mod_override = conn_conf["ModOverride"]
            self.connect_group(conn_src, conn_dst, synapse_id, mod_override)

    # -
    def configure_connections(self, conn_conf):
        """Configure-only circuit connections according to a BlueConfig Connection block

        Args:
            conn_conf: The BlueConfig configuration block (dict)
        """
        log_msg = " * Pathway {:s} -> {:s}".format(conn_conf["Source"], conn_conf["Destination"])
        is_delayed_connection = "Delay" in conn_conf
        if is_delayed_connection:
            log_msg += ":\t[DELAYED] t={0[Delay]:g}, weight={0[Weight]:g}".format(conn_conf)
        if "SynapseConfigure" in conn_conf:
            log_msg += ":\tconfigure with '{:s}'".format(conn_conf["SynapseConfigure"])
        logging.info(log_msg)

        if is_delayed_connection:
            self.setup_delayed_connection(conn_conf)
        else:
            self.configure_group(conn_conf)

    def setup_delayed_connection(self, conn_config):
        raise NotImplementedError("Manager %s doesn't implement delayed connections"
                                  % self.__class__.__name__)

    # -
    def connect_all(self, weight_factor=1, only_gids=None):
        """For every gid access its synapse parameters and instantiate
        all synapses.

        Args:
            weight_factor: Factor to scale all netcon weights (default: 1)
            only_gids: Create connections only for these tgids (default: Off)
        """
        print("Connect all!")
        conn_options = {'weight_factor': weight_factor}
        pop = self._cur_population

        for sgid, tgid, syns_params, extra_params, offset in \
                self._iterate_conn_params(self._src_target_filter, None, only_gids, True):
            if self._load_offsets:
                conn_options["synapses_offset"] = extra_params["synapse_index"][0]
            # Create all synapses. No need to lock since the whole file is consumed
            cur_conn = pop.get_or_create_connection(sgid, tgid, **conn_options)
            self._add_synapses(cur_conn, syns_params, None, offset)

    # -
    def connect_group(self, conn_source, conn_destination, synapse_type_restrict=None,
                      mod_override=None):
        """Instantiates pathway connections & synapses given src-dst

        Args:
            conn_source (str): The target name of the source cells
            conn_destination (str): The target of the destination cells
            synapse_type_restrict(int): Create only given synType synapses
            mod_override (str): ModOverride given for this connection group
        """
        conn_kwargs = {}
        pop = self._cur_population
        logging.debug("Connecting group %s -> %s", conn_source, conn_destination)
        src_tname = TargetSpec(conn_source).name
        dst_tname = TargetSpec(conn_destination).name
        src_target = src_tname and self._target_manager.getTarget(src_tname)
        dst_target = dst_tname and self._target_manager.getTarget(dst_tname)

        for sgid, tgid, syns_params, extra_params, offset in \
                self._iterate_conn_params(src_target, dst_target, mod_override=mod_override):
            if sgid == tgid:
                logging.warning("Making connection within same Gid: %d", sgid)
            if self._load_offsets:
                conn_kwargs["synapses_offset"] = extra_params["synapse_index"][0]

            cur_conn = pop.get_or_create_connection(sgid, tgid, **conn_kwargs)
            if cur_conn.locked:
                continue
            self._add_synapses(cur_conn, syns_params, synapse_type_restrict, offset)
            cur_conn.locked = True

    # -
    def _add_synapses(self, cur_conn, syns_params, syn_type_restrict=None, base_id=0):
        for i, syn_params in enumerate(syns_params):
            if syn_type_restrict and syn_params.synType != syn_type_restrict:
                continue
            point = self._target_manager.locationToPoint(
                cur_conn.tgid, syn_params.isec, syn_params.ipt, syn_params.offset)
            if not point.sclst[0].exists():
                logging.warning("SKIPPED Synapse %s on gid %d. Non-existing target point.",
                                base_id + i, cur_conn.tgid)
            else:
                cur_conn.add_synapse(point, syn_params, base_id + i)

    def get_updated_population_offsets(self, src_target, dst_target):
        sgid_offset = self._src_cell_manager.local_nodes.offset
        tgid_offset = self._cell_manager.local_nodes.offset
        if src_target:
            src_target.set_offset(sgid_offset)
        if dst_target:
            dst_target.set_offset(tgid_offset)
        return sgid_offset, tgid_offset

    # -
    def _iterate_conn_params(self, src_target, dst_target, gids=None, show_progress=False,
                             mod_override=None):
        """A generator which loads synapse data and yields tuples(sgid, tgid, synapses)

        Args:
            src_target: the target to filter the source cells, or None
            dst_target: the target to filter the destination cells, or None
            gids: Use given gids, instead of the circuit target cells. Default: None
            show_progress: Display a progress bar as tgids are processed
        """
        if gids is None:
            gids = self._raw_gids
        if show_progress:
            gids = ProgressBar.iter(gids)
        created_conns_0 = self._cur_population.count()
        sgid_offset, tgid_offset = self.get_updated_population_offsets(src_target, dst_target)

        for base_tgid in gids:
            tgid = base_tgid + tgid_offset
            if dst_target is not None and not dst_target.contains(tgid):
                continue

            # Retrieve all synapses for tgid
            syns_params = self._synapse_reader.get_synapse_parameters(base_tgid, mod_override)
            logging.debug("GID %d Syn count: %d", tgid, len(syns_params))
            cur_i = 0
            syn_count = len(syns_params)

            extra_params = {}
            if self._load_offsets:
                syn_index = self._synapse_reader.get_property(base_tgid, "synapse_index")
                extra_params["synapse_index"] = syn_index.as_numpy()

            sgids = syns_params[syns_params.dtype.names[0]].copy()  # expect src-gid in field 0
            found_conns = 0
            yielded_conns = 0
            _dbg_yielded_src_gids = compat.Vector("i")

            while cur_i < syn_count:
                # Use numpy to get all the synapses of the same gid at once
                sgid = int(sgids[cur_i])
                final_sgid = sgid + sgid_offset
                next_i = numpy.argmax(sgids[cur_i:] != sgid) + cur_i
                if cur_i == next_i:  # last group
                    next_i = syn_count

                if src_target is None or src_target.completeContains(final_sgid):
                    if GlobalConfig.debug_conn == [base_tgid]:
                        _dbg_yielded_src_gids.append(sgid)
                    elif GlobalConfig.debug_conn == [sgid, base_tgid]:
                        log_all(logging.DEBUG, "Connection (%d-%d). Params:\n%s", sgid, base_tgid,
                                syns_params)
                    other_params = {name: prop[cur_i:next_i] for name, prop in extra_params.items()}
                    yield final_sgid, tgid, syns_params[cur_i:next_i], other_params, cur_i
                    yielded_conns += 1

                found_conns += 1
                cur_i = next_i

            if _dbg_yielded_src_gids:
                log_all(logging.DEBUG, "Source GIDs for debug cell: %s", _dbg_yielded_src_gids)
            logging.debug(" > Yielded %d out of %d connections. (Filter by src Target: %s)",
                          yielded_conns, found_conns, src_target and src_target.name)

        created_conns = self._cur_population.count() - created_conns_0
        self._total_connections += created_conns

        all_created = MPI.allreduce(created_conns, MPI.SUM)
        if all_created:
            pathway_repr = "[ALL]"
            if src_target and dst_target:
                pathway_repr = "Pathway {} -> {}".format(src_target.name, dst_target.name)
            logging.info(" * %s. Created %d connections", pathway_repr, all_created)

    # -
    def get_target_connections(self, src_target_name,
                                     dst_target_name,
                                     gidvec=None,
                                     conn_population=None):
        """Retrives the connections between src-dst cell targets

        Args:
             gidvec: (optional) post gids to select (original, w/o offsetting)
             conn_population: restrict the set of connections to be returned
        """
        src_target_spec = TargetSpec(src_target_name)
        dst_target_spec = TargetSpec(dst_target_name)
        src_target = self._target_manager.getTarget(src_target_spec.name) \
            if src_target_spec.name is not None else None
        assert dst_target_spec.name, "No target specified for `get_target_connections`"
        dst_target = self._target_manager.getTarget(dst_target_spec.name)
        gidvec = self._raw_gids if gidvec is None else gidvec
        _, tgid_offset = self.get_updated_population_offsets(src_target, dst_target)

        populations = (conn_population,) if conn_population is not None \
            else self._populations.values()

        for population in populations:
            logging.debug("Connections from population %s", population)
            for raw_tgid in gidvec:
                tgid = raw_tgid + tgid_offset
                if not dst_target.contains(tgid) or tgid not in population:
                    continue
                for conn in population[tgid]:
                    if src_target is None or src_target.completeContains(conn.sgid):
                        yield conn

    # -
    def configure_group(self, conn_config, gidvec=None):
        """Configure connections according to a BlueConfig Connection block

        Args:
            conn_config: The connection configuration dict
            gidvec: A restricted set of gids to configure (original, w/o offsetting)
        """
        src_target = conn_config["Source"]
        dst_target = conn_config["Destination"]
        _properties = {
            "Weight": "weight_factor",
            "SpontMinis": "minis_spont_rate",
            "SynDelayOverride": "syndelay_override"
        }
        syn_params = dict_filter_map(conn_config, _properties)

        # Load eventual mod override helper
        if "ModOverride" in conn_config:
            logging.info("   => Overriding mod: %s", conn_config["ModOverride"])
            override_helper = conn_config["ModOverride"] + "Helper"
            Nd.load_hoc(override_helper)
            assert hasattr(Nd.h, override_helper), \
                "ModOverride helper doesn't define hoc template: " + override_helper

        for conn in self.get_target_connections(src_target, dst_target, gidvec):
            for key, val in syn_params.items():
                setattr(conn, key, val)
            if "ModOverride" in conn_config:
                conn.override_mod(conn_config['_hoc'])
            if "SynapseConfigure" in conn_config:
                conn.add_synapse_configuration(conn_config["SynapseConfigure"])

    # -
    def configure_group_delayed(self, conn_config, gidvec=None):
        """Update instantiated connections with configuration from a
        'Delayed Connection' blocks.
        """
        self.update_connections(conn_config["Source"],
                                conn_config["Destination"],
                                gidvec,
                                conn_config.get("SynapseConfigure"),
                                conn_config.get("Weight"))

    # Live connections update
    # -----------------------
    @timeit(name="connUpdate", verbose=False)
    def update_connections(self, src_target, dst_target, gidvec=None,
                                 syn_configure=None, weight=None, **syn_params):
        """Update params on connections that are already instantiated.

        Args:
            src_target: Name of Source Target
            dst_target: Name of Destination Target
            gidvec: A list of gids to apply configuration. Default: all
            syn_configure: A hoc configuration string to apply to the synapses
            weight: new weights for the netcons
            **syn_params: Keyword arguments of synapse properties to be changed
                e.g. conductance: g=xyz
        """
        if syn_configure is None and weight is None and not syn_params:
            logging.warning("No synpases parameters being updated for Targets %s->%s",
                            src_target, dst_target)
            return

        updated_conns = 0
        for conn in self.get_target_connections(src_target, dst_target, gidvec):
            if weight is not None:
                updated_conns += 1
                conn.update_weights(weight)
            if syn_configure is not None:
                conn.configure_synapses(syn_configure)
            if syn_params:
                conn.update_synpase_parameters(**syn_params)

        logging.info("Updated %d conns", updated_conns)

    def restart_events(self):
        """After restore, restart the artificial events (replay and spont minis)
        """
        for conn in self.all_connections():
            conn.restart_events()

    # ------------------------------------------------------------------
    # Delete, Disable / Enable
    # ------------------------------------------------------------------
    def delete(self, sgid, tgid, population_ids=None):
        """Deletes a connection given source and target gids.

        NOTE: Contrary to disable(), deleting a connection cannot be undone,
        however it may help saving computational resources.

        Args:
            sgid: The pre-gid of the cell
            tgid: The post-gid of the cell
            population_ids: The population selector. Default: all
        """
        for pop in self.find_populations(population_ids):
            pop.delete(sgid, tgid)

    def disable(self, sgid, tgid, also_zero_conductance=False, population_ids=None):
        """Disable a connection, its netcons and optionally synapses.

        NOTE: Disabling a connection before calling init() prevents
        it from being instantiated in CoreNeuron.

        Args:
            sgid: The pre-gid of the cell
            tgid: The post-gid of the cell
            also_zero_conductance: Also sets synapses' conductances
                to zero. Default: False
            population_ids: The population selector. Default: all
        """
        for pop in self.find_populations(population_ids):
            c = pop.get_connection(sgid, tgid)
            c.disable(also_zero_conductance)
            self._disabled_conns[tgid].append(c)

    def reenable(self, sgid, tgid, population_ids=None):
        """(Re)enable a connection from given populations.
        """
        allowed_pops = self.find_populations(population_ids)
        delete_indexes = []
        for i, conn in enumerate(self._disabled_conns[tgid]):
            if conn.sgid == sgid and any((p.src_id, p.dst_id) == conn.population_id
                                         for p in allowed_pops):
                conn.enable()
                delete_indexes.append(i)
        self._disabled_conns[tgid] = \
            numpy.delete(self._disabled_conns[tgid], delete_indexes).tolist()

    def reenable_all(self, post_gids=None):
        """Re-enables all disabled connections

        Args:
            post_gids: The list of target gids to enable (Default: all)
        """
        gids = self._raw_gids if post_gids is None else post_gids
        offset = self._cell_manager.local_nodes.offset
        for tgid in gids:
            tgid += offset
            for c in self._disabled_conns[tgid]:
                c.enable()
            del self._disabled_conns[tgid][:]

    # GROUPS
    # ------
    def delete_group(self, post_gids, pre_gids=None, population_ids=None):
        """Delete a number of connections given pre and post gid lists.
           Note: None is neutral and will match all gids.

        Args:
            post_gids: The target gids of the connections to be disabled
                Use None for all post-gids
            pre_gids: idem for pre-gids. [Default: None -> all)
            population_ids: A int/tuple of populations ids. Default: all
        """
        for pop in self.find_populations(population_ids):
            pop.delete_group(post_gids, pre_gids)

    def disable_group(self, post_gids, pre_gids=None,
                            also_zero_conductance=False,
                            population_ids=None):
        """Disable a number of connections given pre and post gid lists.

        Args:
            post_gids: The target gids of the connections to be deleted
            pre_gids: idem for pre-gids. [Default: None -> all)
            also_zero_conductance: Also sets synapse conductance to 0
            population_ids: A int/tuple of populations ids. Default: all
        """
        for pop in self.find_populations(population_ids):
            for conn in pop.get_connections(post_gids, pre_gids):
                self._disabled_conns[conn.tgid].append(conn)
                conn.disable(also_zero_conductance)

    def reenable_group(self, post_gids, pre_gids=None, population_ids=None):
        """Enable a number of connections given lists of pre and post gids.
        Note: None will match all gids.
        """
        if post_gids is None:
            post_gids = self._raw_gids
        offset = self._cell_manager.local_nodes.offset
        pre_gids = set(pre_gids)
        allowed_pops = self.find_populations(population_ids)

        for tgid in post_gids:
            tgid += offset
            to_delete = []
            for i, conn in enumerate(self._disabled_conns[tgid]):
                if conn.sgid in pre_gids and \
                        any((p.src_id, p.dst_id) == conn.population_id
                            for p in allowed_pops):
                    conn.enable()
                    to_delete.append(i)

            self._disabled_conns[tgid] = \
                numpy.delete(self._disabled_conns[tgid], to_delete).tolist()

    def get_disabled(self, post_gid=None):
        """Returns the list of disabled connections, optionally for a
        given post-gid.
        """
        if post_gid is not None:
            return self._disabled_conns[post_gid]
        return chain.from_iterable(self._disabled_conns.values())

    def _unlock_all_connections(self):
        """Unlock all, mainly when we load a new connectivity source"""
        for conn in self.all_connections():
            conn.locked = False

    def finalize(self, base_seed=0, sim_corenrn=False, *, _conn_type="synapses", **conn_params):
        """Instantiates the netcons and Synapses for all connections.

        Note: All weight scalars should have their final values.

        Args:
            base_seed: optional argument to adjust synapse RNGs (default=0)
            sim_corenrn: Finalize accordingly in case we target CoreNeuron
            _conn_type: (Internal) A string repr of the connectivity type
            conn_params: Additional finalize parameters for the specific _finalize_conns
                E.g. replay_mode (Default: Auto-Detect) Use DISABLED to skip replay
                and COMPLETE to instantiate VecStims in all synapses

        """
        self._synapse_reader = None  # Destroy to release memory (all cached params)
        logging.info("Instantiating %s... Params: %s", _conn_type, str(conn_params))
        n_created_conns = 0

        for popid, pop in self._populations.items():
            attach_src = (pop.src_id == 0 or not pop.virtual_source  # real populations
                          or pop.virtual_source and bool(sim_corenrn))  # Req'd for replay
            conn_params["attach_src_cell"] = attach_src
            logging.info(" * Connections among %s -> %s, attach src: %s",
                         pop.src_name or "(base)", pop.dst_name or "(base)", attach_src)

            for tgid, conns in ProgressBar.iter(pop.items(), name="Pop:" + str(popid)):
                n_created_conns += self._finalize_conns(
                    tgid, conns, base_seed, sim_corenrn, **conn_params)

        all_ranks_total = MPI.allreduce(n_created_conns, MPI.SUM)
        logging.info(" => Created %d %s", all_ranks_total, _conn_type)
        return all_ranks_total

    def _finalize_conns(self, tgid, conns, base_seed, sim_corenrn, *, reverse=False, **kwargs):
        """ Low-level handling of finalizing connections belonging to a target gid.
        By default it calls finalize on each cell.
        """
        # Note: *kwargs normally contains 'replay_mode' but may differ for other types
        metype = self._cell_manager.getMEType(tgid)
        n_created_conns = 0
        if reverse:
            conns = reversed(conns)
        for conn in conns:  # type: Connection
            n_created_conns += conn.finalize(metype, base_seed, skip_disabled=sim_corenrn, **kwargs)
        return n_created_conns

    # -
    def replay(self, *_, **_kw):
        logging.warning("Replay is not available in %s", self.__class__.__name__)


# ##############
# Helper methods
# ##############

def edge_node_pop_names(edge_file, edge_pop_name, src_pop_name=None, dst_pop_name=None):
    """Find/decides the node populations names from several edge configurations

    Args:
        edge_file: The edge file to extract the population names from
        edge_pop_name: The name of the edge population
        src_pop_name: Overriding source pop name
        dst_pop_name: Overriding target population name

    Returns: tuple of the src-dst population names. Any can be None if not available
    """
    if src_pop_name and dst_pop_name or not edge_file.endswith(".h5"):
        return src_pop_name, dst_pop_name
    # Get src-dst pop names, allowing current ones to override
    src_dst_pop_names = _edge_meta_get_node_populations(edge_file, edge_pop_name) \
                        or _edge_to_node_population_names(edge_pop_name)
    if src_dst_pop_names:
        if src_pop_name is None:
            src_pop_name = src_dst_pop_names[0]
        if dst_pop_name is None:
            dst_pop_name = src_dst_pop_names[1]
    return src_pop_name, dst_pop_name


@run_only_rank0
def _edge_meta_get_node_populations(edge_file, edge_pop_name) -> [None, tuple]:
    import h5py
    f = h5py.File(edge_file, 'r')
    if "edges" not in f:
        return None
    edge_group = f["edges"]
    if not edge_pop_name:
        assert len(edge_group) == 1, "multi-population edges require manual selection"
        edge_pop_name = next(iter(edge_group.keys()))
    edge_pop = edge_group[edge_pop_name]

    try:
        return (edge_pop["source_node_id"].attrs["node_population"],
                edge_pop["target_node_id"].attrs["node_population"])
    except KeyError:
        logging.warning("Edges don't have 'node_population' attribute")
    return None


def _edge_to_node_population_names(edge_pop_name):
    """Obtain the node source and destination population names from an edge population name
    """
    if edge_pop_name is None or "__" not in edge_pop_name:
        return None
    logging.info("(Compat) Using edge population name to know intervening nodes")
    pop_infos = edge_pop_name.split("__")
    src_pop = pop_infos[0]
    dst_pop = pop_infos[1] if len(pop_infos) > 2 else src_pop
    return src_pop, dst_pop


def _get_projection_population_id(projection):
    """Check projection config for overrides to the population ID
    """
    pop_id = None
    if "PopulationID" in projection:
        pop_id = int(projection["PopulationID"])
    if pop_id == 0:
        raise ConfigurationError("PopulationID 0 is not allowed")
    # If the projections are to be merged with base connectivity and the base
    # population is unknown, with Sonata pop we need a way to explicitly request it.
    # Note: gid offsetting must have been previously done
    if projection.get("AppendBasePopulation"):
        assert pop_id is None, "AppendBasePopulation is incompatible with PopulationID"
        log_verbose("Appending projection to base connectivity (AppendBasePopulation)")
        pop_id = 0
    return pop_id


# ######################################################################
# SynapseRuleManager
# ######################################################################
class SynapseRuleManager(ConnectionManagerBase):
    """
    The SynapseRuleManager is designed to encapsulate the creation of
    synapses for BlueBrain simulations, handling the data coming from
    the circuit file. If the BlueConfig file provides any Connection
    Rules, those override which synapses are created.

    Note that the Connection rules are processed with the assumption
    that they come in the config file from more general to more specific.
    E.g.: A column->column connection should come before
    layer 4 -> layer 2 which should come before L4PC -> L2PC.

    Once all synapses are prepared with final weights, the Netcons can be
    created.
    """

    CONNECTIONS_TYPE = SynapseReader.SYNAPSES

    def __init__(self, circuit_conf, target_manager, cell_manager, src_cell_manager=None, **kw):
        """Initializes a Connection/Edge manager for standard METype synapses

        Args:
            circuit_conf: The configuration object/dict
            target_manager: The (hoc-level) target manager
            cell_manager: The destination cell population manager
            src_cell_manager: The source cell population manager [Default: same as destination]
        """
        super().__init__(circuit_conf, target_manager, cell_manager, src_cell_manager, **kw)
        # SynapseRuleManager opens synapse file and init populations
        syn_source = circuit_conf.get("nrnPath")
        if syn_source:
            logging.info("Init %s. Options: %s", type(self).__name__, kw)
            self.open_edge_location(syn_source, circuit_conf, **kw)

    # -
    def finalize(self, base_seed=0, sim_corenrn=False, **kwargs):
        """Create the actual synapses and netcons. See super() docstring
        """
        # CoreNeuron will handle replays automatically with its own PatternStim
        kwargs.setdefault("replay_mode", ReplayMode.NONE if sim_corenrn else ReplayMode.AS_REQUIRED)
        super().finalize(base_seed, sim_corenrn, **kwargs)

    def _finalize_conns(self, tgid, conns, base_seed, sim_corenrn, **kw):
        # Note: (Compat) neurodamus hoc finalizes connections in reversed order.
        return super()._finalize_conns(tgid, conns, base_seed, sim_corenrn, reverse=True, **kw)

    # -
    def setup_delayed_connection(self, conn_config):
        """Setup delayed connection weights for synapse initialization.

        Find source and target gids and the associated connection,
        and add the delay and weight to their delay vectors.

        Args:
            conn_config: Connection configuration parsed from BlueConfig
        """
        src_target_name = conn_config["Source"]
        dst_target_name = conn_config["Destination"]
        delay = conn_config["Delay"]
        new_weight = conn_config.get("Weight", .0)

        for conn in self.get_target_connections(src_target_name, dst_target_name):
            conn.add_delayed_weight(delay, new_weight)

    # -
    @timeit(name="Replay inject")
    def replay(self, spike_manager, src_target_name, dst_target_name, start_delay=.0):
        """Create special netcons to trigger timed spikes on those synapses.

        Args:
            spike_manager: map of gids (pre-synaptic) with spike times
            src_target_name: Source population:target of the replay connections
            dst_target_name: Target whose gids should be replayed
            start_delay: Dont deliver events before t=start_delay
        """
        log_verbose("Applying replay map with %d src cells...", len(spike_manager))
        replayed_count = 0

        # Dont deliver events in the past
        if Nd.t > start_delay:
            start_delay = Nd.t
            log_verbose("Restore: Delivering events only after t=%.4f", start_delay)

        src_pop_offset = self.src_pop_offset

        for conn in self.get_target_connections(src_target_name, dst_target_name):
            raw_sgid = conn.sgid - src_pop_offset
            if raw_sgid not in spike_manager:
                continue
            conn.replay(spike_manager[raw_sgid], start_delay)
            replayed_count += 1

        total_replays = MPI.allreduce(replayed_count, MPI.SUM)
        if MPI.rank == 0:
            if total_replays == 0:
                logging.warning("No connections were injected replay stimulus")
            else:
                logging.info(" => Replaying on %d connections", total_replays)
        return total_replays