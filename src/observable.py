class Observable(object):
    def __init__(self, events):
      self.callbacks = {}

      for event in events:
          self.callbacks[event] = []
  
    def on(self, event, cb):
        if event not in self.callbacks:
            raise Exception("Event %s not supported" % event)
        
        self.callbacks[event].append(cb)

    def emit(self, event, *attrs):
        for cb in self.callbacks[event]:
            cb(**attrs)