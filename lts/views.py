from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants
from django import forms
from .helper_functions import *
from otree.api import safe_json
from time import time

########## Views

def skip_rest_of_test(page):
    "Decides whether pages are displayed or not."
    if is_test_phase(page) and page.player.particip.test_time_left <= 0:
        return False            # skip pages until no test phase page no more
    else:
        return True


class OrderRelease(Page):
    "Page definition for order releases"

    form_model = models.Player
    form_fields = ['click_show']
    # timeout_seconds = 20

    def is_displayed(self):
        return skip_rest_of_test(self)

    def post(self, request, **kwargs):
        "Override the default post behavior"

        orders = get_releasable_orders(self, is_test_phase(self))
        current_period = self.player.period
        start_time = request.POST["start_time"]
        end_time = int(time())
        diff_secs = end_time - int(start_time)

        self.player.particip.test_time_left -= diff_secs
        self.player.particip.save()

        if models.debug:
            print("Released Orders:")
            for k in request.POST:
                print(k, request.POST[k])

        # save released orders
        # if not self.player.release_last_week_round:
        print (request.POST)
        print("orders: ", orders)
        for order in orders:
                if "order_"+str(order.get_order_id()) in request.POST and \
                   request.POST["order_"+str(order.get_order_id())]:

                    order.set_release(current_period.start)
                    order.save()

        return super(OrderRelease, self).post(request, **kwargs)


    def vars_for_template(self):
        "This method defines the variables which are handed over to the html file."

        # set timeout (not working dynamically)
        # self.timeout_seconds = self.player.particip.test_time_left

        releasable_orders = get_releasable_orders(self,True)
        releasable_orders_ids = [ x.get_order_id() for x in releasable_orders ]
        sum_costs_ob = get_sum_costs(self)
        last_week_orders = []
        if self.player.release_last_week_round:
            nr = self.player.subsession.session.config['start_wip_count']
            last_week_orders = releasable_orders[:nr]
            releasable_orders = releasable_orders[nr:]
            # all_orders = get_all_orders(self)
            # last_week_orders = [o for o in all_orders if
            #                     o.release_date is not None]

        print("Period: ", self.player.period)
        print("Particip: ", self.player.particip)

        return {'releasable_orders': releasable_orders,
                'releasable_orders_ids': releasable_orders_ids,
                'released_orders': get_released_orders(self),
                'orders': self.player.particip.orders.all(),
                'all_orders': get_all_orders(self),
                'last_week_orders': last_week_orders,
                'last_week_order_ids': [x.get_order_id() for x in last_week_orders],
                'is_last_week_release_round': self.player.release_last_week_round,
                'costs': self.player.costs,
                'sum_costs_object': sum_costs_ob,
                'sum_costs': sum_costs_ob.wip + sum_costs_ob.fgi + sum_costs_ob.bo,
                'start_time': int(time()),
                'seconds_left_test': self.player.particip.test_time_left,
                'is_test': is_test_phase(self),
                'show_howto_info': is_test_phase(self),
                'datetimetext': "Morgen",

                'wip': self.player.costs.wip,
                'fgi': self.player.costs.fgi,
                'bo': self.player.costs.bo,
                'wipfgibo': self.player.costs.wip + self.player.costs.fgi + self.player.costs.bo,
                'sum_wip': sum_costs_ob.wip,
                'sum_fgi': sum_costs_ob.fgi,
                'sum_bo': sum_costs_ob.bo,

                'period': self.player.period,
                'player_id': self.player.id,
                'finished_orders': get_finished_orders(self),
                'processing': get_processing_orders(self),
                'flow_time': "{0:.2f}".format(get_last_known_flow_time(self)).replace(".",","),

                'current_day': self.player.period.start-1,
                'rush_order_days': Constants.rush_order_days,
                'flow_time_year': self.player.subsession.session.config['flow_time_last_year'],
        }

    def before_next_page(self):
        "Simulates the production system."

        simulate(self)          # simulate everything


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):

    # timeout_seconds = 30

    def is_displayed(self):
        return skip_rest_of_test(self)


    def vars_for_template(self):
        "This method defines the variables which are handed over to the html file."

        sum_costs_ob = get_sum_costs(self)


        return {'releasable_orders': get_releasable_orders(self),
                'released_orders': get_released_orders(self),
                'costs': self.player.costs,

                'seconds_left_test': self.player.particip.test_time_left,
                'is_test': is_test_phase(self),
                'start_time': int(time()),
                'datetimetext': "Abend",
                'wip': self.player.costs.wip,
                'fgi': self.player.costs.fgi,
                'bo': self.player.costs.bo,
                'wipfgibo': self.player.costs.wip + self.player.costs.fgi + self.player.costs.bo,
                'sum_wip': sum_costs_ob.wip,
                'sum_fgi': sum_costs_ob.fgi,
                'sum_bo': sum_costs_ob.bo,

                'period': self.player.period,
                'orders': self.player.particip.orders.all(),
                'finished_orders': get_finished_orders(self),
                'processing': get_processing_orders(self),
                'flow_time': "{0:.2f}".format(self.player.flow_time).replace(".",","),
                'sum_costs_object': sum_costs_ob,
                'sum_costs': sum_costs_ob.wip + sum_costs_ob.fgi + sum_costs_ob.bo,
                'current_day': self.player.period.end,
                'flow_time_year': self.player.subsession.session.config['flow_time_last_year'],
        }

    def post(self, request, **kwargs):
        "Override the default post behavior"

        start_time = request.POST["start_time"]
        end_time = int(time())
        diff_secs = end_time - int(start_time)
        self.player.particip.test_time_left -= diff_secs
        self.player.particip.save()

        return super(Results, self).post(request, **kwargs)


    def before_next_page(self):

        sum_costs_ob = get_sum_costs(self)
        sum_costs = sum_costs_ob.wip + sum_costs_ob.fgi + sum_costs_ob.bo

        if is_test_phase(self):
            # reset all orders
            for o in get_all_orders(self):
                o.nr = None
                o.time_until_finished = o.full_processing_time
                o.release_date = None
                o.is_processing = False
                o.fgi_arrived_date = None
                o.sent_date = None
                o.save()
            csts = Costs(wip=0, fgi=0, bo=0)
            csts.save()

            # reset player
            self.player.costs = csts
            self.player.flow_time = None

            # set particip object
            self.player.particip.in_current_period = 1
            if self.player.particip.test_time_left < 1:
                self.player.particip.test_time_left = 0
            self.player.particip.save()


        self.participant.vars['sum_costs'] = sum_costs


class TimePage(Page):

    def is_displayed(self):
        return skip_rest_of_test(self)

    def vars_for_template(self):
        "This method defines the variables which are handed over to the html file."

        sum_costs_ob = get_sum_costs(self)

        return {'current_day': safe_json(self.player.period.start-1),
                'end_day': safe_json(self.player.period.end),
        }

    def before_next_page(self):
        self.player.particip.test_time_left -= 5
        self.player.particip.save()


class EndPage(Page):

    def is_displayed(self):     # only show at last round
        return self.player.round_number == models.Constants.num_rounds


class WaitPageEndTest(WaitPage):

    def is_displayed(self):     # only show at last round
        return self.player.round_number == models.Constants.max_test_rounds


class Info(Page):
    def is_displayed(self):     # only show at last round
        return self.player.round_number == models.Constants.max_test_rounds+1

    def before_next_page(self):
        self.player.costs.wip = 0
        self.player.costs.fgi = 0
        self.player.costs.bo = 0
        self.player.costs.save()


class WelcomeExperiment(Page):
    def is_displayed(self):     # only show after test phase
        return self.player.round_number == models.Constants.max_test_rounds+1

page_sequence = [
    WelcomeExperiment,
    OrderRelease,
    # TimePage,
    Results,
    ResultsWaitPage,
    WaitPageEndTest,
    Info
    # EndPage
]
