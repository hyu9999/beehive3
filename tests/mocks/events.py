from typing import List


class EventSource:
    kafka_topic_name: str
    event_types: List[str]
    description: str


class CompanyDynamicsEventSource(EventSource):
    pass


class NewsEventSource(EventSource):
    pass


class CapitalFlowEventSource(EventSource):
    pass


class EconomicDataEventSource(EventSource):
    pass


class QuoteFeedEventSource(EventSource):
    pass


class UserActionEventSource(EventSource):
    pass


class ScheduledEventSource(EventSource):
    pass


class MarketEventSource(EventSource):
    pass


class FundEventSource(EventSource):
    pass


class ManualTrigger(EventSource):
    pass


mock_event_source_dict = {es.__name__: es for es in EventSource.__subclasses__()}
