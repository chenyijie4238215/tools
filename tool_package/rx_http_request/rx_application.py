from PyQt5.QtCore import QEvent, QTimer
from PyQt5.QtWidgets import QApplication
from rx.core import Disposable
from rx.disposables import SingleAssignmentDisposable, CompositeDisposable
from rx.concurrency.schedulerbase import SchedulerBase
import uuid

from tool_function.decorator import singleton


@singleton
class MainThreadScheduler(SchedulerBase):
    def __init__(self, app=QApplication.instance()):
        self._app = app

    def _qtimer_schedule(self, time, action, state, periodic=False):
        scheduler = self
        msecs = self.to_relative(time)
        disposable = SingleAssignmentDisposable()
        periodic_state = [state]

        def interval():
            if periodic:
                periodic_state[0] = action(periodic_state[0])
            else:
                disposable.disposable = action(scheduler, state)

        timer_name = uuid.uuid1()
        single_shot = not periodic
        self._app.on_interval(timer_name, single_shot, interval, msecs)

        def dispose():
            self._app.on_dispose(timer_name)

        return CompositeDisposable(disposable, Disposable.create(dispose))

    def schedule(self, action, state=None):
        return self._qtimer_schedule(0, action, state)

    def schedule_relative(self, duetime, action, state=None):
        return self._qtimer_schedule(duetime, action, state)

    def schedule_absolute(self, duetime, action, state=None):
        duetime = self.to_datetime(duetime)
        return self._qtimer_schedule(duetime, action, state)

    def schedule_periodic(self, period, action, state=None):
        return self._qtimer_schedule(period, action, state, periodic=True)


class ScheduleEvent(QEvent):
    _type = QEvent.None_

    def __init__(self, timer_name=None, single_shot=True, interval=None, msecs=0, is_stop=False):
        super(ScheduleEvent, self).__init__(ScheduleEvent.event_type())
        self.timer_name = timer_name
        self.single_shot = single_shot
        self.interval = interval
        self.msecs = msecs
        self.is_stop = is_stop

    @staticmethod
    def event_type():
        if ScheduleEvent._type == QEvent.None_:
            ScheduleEvent._type = QEvent.registerEventType()
        return ScheduleEvent._type


class RxTimer(QTimer):
    def __init__(self, name):
        super(RxTimer, self).__init__()
        self.name = name


class RxApplication(QApplication):
    def __init__(self, *args, **argv):
        super(RxApplication, self).__init__(*args, **argv)
        self._timers = set()
        self.installEventFilter(self)
        MainThreadScheduler(self)

    def eventFilter(self, obj, event):
        if obj == self and event.type() == ScheduleEvent.event_type():
            if event.is_stop:
                self.stop_rx_timer(event.time_name)
            else:
                self.start_rx_timer(event.timer_name, event.single_shot, event.interval, event.msecs)
            return True
        return False

    def stop_rx_timer(self, time_name):
        timer = None
        for t in self._timers:
            if t.name == time_name:
                timer = t
                break
        if timer:
            timer.stop()
            timer.disconnect()
            self._timers.remove(timer)

    def start_rx_timer(self, timer_name, single_shot, interval, msecs):
        def on_timeout():
            interval()
            if single_shot:
                self.stop_rx_timer(timer_name)
        timer = RxTimer(timer_name)
        timer.setSingleShot(single_shot)
        timer.setInterval(msecs)
        timer.timeout.connect(on_timeout)
        timer.start()
        self._timers.add(timer)

    def on_interval(self, timer_name, single_shot, interval, msecs):
        self.postEvent(self, ScheduleEvent(timer_name, single_shot, interval, msecs))

    def on_dispose(self, timer_name):
        self.postEvent(self, ScheduleEvent(timer_name, is_stop=True))
