from loguru import logger

from .diagnostic import VerosDiagnostic
from .. import veros_method


class NPZDMonitor(VerosDiagnostic):
    """Diagnostic monitoring nutrients and plankton concentrations
    """

    name = 'npzd'
    output_frequency = None
    restart_attributes = []

    def __init__(self, setup):
        self.save_graph = False
        self.graph_attr = {
            'splines': 'ortho',
            'center': 'true',
            'nodesep': '0.05',
            'node': 'square'
        }

        self.output_variables = []
        self.surface_out = []
        self.bottom_out = []
        self.po4_total = 0
        self.dic_total = 0

    @veros_method
    def initialize(self, vs):
        cell_volume = vs.area_t[2:-2, 2:-2, np.newaxis] * vs.dzt[np.newaxis, np.newaxis, :] * vs.maskT[2:-2, 2:-2, :]

        po4_sum = vs.phytoplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.detritus[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.zooplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.po4[2:-2, 2:-2, :, vs.tau]

        self.po4_total = np.sum(po4_sum * cell_volume)

        if vs.enable_carbon:
            dic_sum = vs.phytoplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.detritus[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.zooplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.dic[2:-2, 2:-2, :, vs.tau]

            self.dic_total = np.sum(dic_sum * cell_volume)

    def diagnose(self, vs):
        pass

    @veros_method
    def output(self, vs):
        """Print NPZD interaction graph
        """
        if self.save_graph:
            from graphviz import Digraph
            npzd_graph = Digraph('npzd_dynamics', filename='npzd_dynamics.gv')
            label_prefix = '\\tiny '
            label_prefix = ''

            for tracer in vs.npzd_tracers:
                npzd_graph.node(tracer)

            for rule in vs.npzd_rules:
                npzd_graph.edge(rule.source, rule.sink, label=label_prefix + rule.label, lblstyle='sloped, above')

            for rule in vs.npzd_pre_rules:
                npzd_graph.edge(rule.source, rule.sink, label=label_prefix + rule.label, style='dotted', lblstyle='sloped, above')

            for rule in vs.npzd_post_rules:
                npzd_graph.edge(rule.source, rule.sink, label=label_prefix + rule.label, style='dashed', lblstyle='sloped, above')

            if vs.sinking_speeds:
                npzd_graph.node('Bottom', shape='square')
                for sinker in vs.sinking_speeds:
                    npzd_graph.edge(sinker, 'Bottom', label=label_prefix + 'sinking', lblstyle='sloped, above')

            self.save_graph = False
            # npzd_graph.save()
            npzd_graph.render('npzd_graph', view=False)

        """
        Total phosphorus should be (approximately) constant
        """
        cell_volume = vs.area_t[2:-2, 2:-2, np.newaxis] * vs.dzt[np.newaxis, np.newaxis, :] * vs.maskT[2:-2, 2:-2, :]

        po4_sum = vs.phytoplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.detritus[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.zooplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_PN\
                  + vs.po4[2:-2, 2:-2, :, vs.tau]

        if vs.enable_carbon:
            dic_sum = vs.phytoplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.detritus[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.zooplankton[2:-2, 2:-2, :, vs.tau] * vs.redfield_ratio_CN\
                      + vs.dic[2:-2, 2:-2, :, vs.tau]


        po4_total = np.sum(po4_sum * cell_volume)
        logger.warning(' total phosphorus: {}, relative change: {}'.format(po4_total, (po4_total - self.po4_total)/self.po4_total))
        self.po4_total = po4_total[...]

        if vs.enable_carbon:
            dic_total = np.sum(dic_sum * cell_volume)
            logger.warning(' total DIC: {}, relative change: {}'.format(dic_total, (dic_total - self.dic_total)/self.dic_total))
            self.dic_total = dic_total.copy()

        for var in self.output_variables:
            if var in vs.recycled:
                recycled_total = np.sum(vs.recycled[var][2:-2, 2:-2, :] * cell_volume)
            else:
                recycled_total = 0

            if var in vs.mortality:
                mortality_total = np.sum(vs.mortality[var][2:-2, 2:-2, :] * cell_volume)
            else:
                mortality_total = 0

            if var in vs.net_primary_production:
                npp_total = np.sum(vs.net_primary_production[var][2:-2, 2:-2, :] * cell_volume)
            else:
                npp_total = 0

            if var in vs.grazing:
                grazing_total = np.sum(vs.grazing[var][2:-2, 2:-2, :] * cell_volume)
            else:
                grazing_total = 0

            logger.warning(' total recycled {}: {}'.format(var, recycled_total))
            logger.warning(' total mortality {}: {}'.format(var, mortality_total))
            logger.warning(' total npp {}: {}'.format(var, npp_total))
            logger.warning(' total grazed {}: {}'.format(var, grazing_total))

        for var in self.surface_out:
            logger.warning(' mean {} surface concentration: {} mmol/m^3'.format(var, vs.npzd_tracers[var][vs.maskT[:, :, -1]].mean()))

        for var in self.bottom_out:
            logger.warning(' mean {} bottom concentration: {} mmol/m^3'.format(var, vs.npzd_tracers[var][vs.bottom_mask].mean()))

    def read_restart(self, vs):
        pass

    def write_restart(self, vs, outfile):
        pass
