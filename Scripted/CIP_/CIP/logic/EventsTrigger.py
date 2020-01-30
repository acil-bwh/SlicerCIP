class EventsTrigger(object):
    """ 'Abstract' class that has a mechanism to subscribe and trigger events
    """
    def __init__(self):
        self.__events__ = []
        self.__eventsCallbacks__ = {}
        self.__eventsCount__ = 0
    
    @property
    def events(self):
        return self.__events__

    def setEvents(self, eventsList):
        """ Set the events that the class is handling
        :param eventsList:
        :return:
        """
        self.__events__ = eventsList

    def addObservable(self, eventTypeId, callbackFunction):
        """ Add a function that will be invoked when the corresponding event is triggered.
        Ex: myWidget.addObservable(myWidget.EVENT_BEFORE_NEXT, self.onBeforeNextClicked)
        :param eventTypeId: public id if the event exposed by the class
        :param callbackFunction: function that will be invoked when the event is triggered
        :return: identifier for this observable (that can be used to remove it)
        """
        if eventTypeId not in self.events:
            raise Exception("Event not recognized. Make sure that the event belongs to the class and you called the function 'setEvents'")

        # Add the event to the list of funcions that will be called when the matching event is triggered
        self.__eventsCallbacks__[self.__eventsCount__] = (eventTypeId, callbackFunction)
        self.__eventsCount__ += 1
        return self.__eventsCount__ - 1

    def removeObservable(self, eventId):
        """ Remove an observable from the list of callbacks to be invoked when an event is triggered
        :param eventId: internal id that was given when the observable was created
        """
        if eventId in self.__eventsCallbacks__:
            self.__eventsCallbacks__.pop(eventId)

    def removeAllObservables(self):
        """ Remove all the current observables. No events will be captured anymore
        """
        self.__eventsCallbacks__.clear()

    def getAllObservables(self):
        """ Get a list of (id, tuple) with all the current observables
        :return:
        """
        return list(self.__eventsCallbacks__.items())

    def triggerEvent(self, eventType, *params):
        """Trigger one of the possible events from the object.
        Ex:    self._triggerEvent_(self.EVENT_BEFORE_NEXT) """
        for callbackFunction in (item[1] for item in self.__eventsCallbacks__.values() if item[0] == eventType):
            callbackFunction(*params)
