from proj.core import States
from proj.core.middlewares import StateResolverMiddleware

from .views import *


def setup_routes():
    sr = StateResolverMiddleware

    sr.add_state(States.WAITING_FOR_TRIGGER, TriggerReceivedView)
    sr.add_state(States.WAITING_FOR_START_CHOICE, StartActionClickedView)
