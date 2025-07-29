import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import time
from It1_interfaces.EventSystem import EventPublisher, EventType, Event, event_publisher

# === עוזרים כלליים ===
def create_callback(storage: list, label: str = ""):
    def callback(event: Event):
        storage.append((label, event))
    return callback

# === TEST 1: Subscribe & Publish ===
def test_subscribe_and_publish():
    publisher = EventPublisher()
    events = []
    cb = create_callback(events, "cb1")

    publisher.subscribe(EventType.GAME_START, cb)
    publisher.publish(EventType.GAME_START, {"msg": "Let's go!"})

    assert len(events) == 1
    label, event = events[0]
    assert label == "cb1"
    assert event.type == EventType.GAME_START
    assert event.data == {"msg": "Let's go!"}
    assert isinstance(event.timestamp, int)

# === TEST 2: Multiple Callbacks for One Event ===
def test_multiple_callbacks():
    publisher = EventPublisher()
    calls = []

    cb1 = create_callback(calls, "cb1")
    cb2 = create_callback(calls, "cb2")

    publisher.subscribe(EventType.MOVE_MADE, cb1)
    publisher.subscribe(EventType.MOVE_MADE, cb2)
    publisher.publish(EventType.MOVE_MADE, {"move": "a2a4"})

    assert len(calls) == 2
    labels = [label for label, _ in calls]
    assert "cb1" in labels and "cb2" in labels

# === TEST 3: Unsubscribe ===
def test_unsubscribe():
    publisher = EventPublisher()
    calls = []

    cb = create_callback(calls, "cb")
    publisher.subscribe(EventType.GAME_END, cb)
    publisher.unsubscribe(EventType.GAME_END, cb)
    publisher.publish(EventType.GAME_END)

    assert len(calls) == 0  # לא נקרא

# === TEST 4: Publish Without Subscribers ===
def test_publish_no_subscribers():
    publisher = EventPublisher()
    try:
        publisher.publish(EventType.PIECE_CAPTURED, {"who": "BQ"})
    except Exception:
        pytest.fail("Exception occurred during publish with no subscribers")

# === TEST 5: Callback Raises Exception But Doesn’t Crash Others ===
def test_callback_exception():
    publisher = EventPublisher()
    calls = []

    def good_cb(event): calls.append("good")
    def bad_cb(event): raise ValueError("Oops")

    publisher.subscribe(EventType.KING_CAPTURED, good_cb)
    publisher.subscribe(EventType.KING_CAPTURED, bad_cb)

    publisher.publish(EventType.KING_CAPTURED)

    assert "good" in calls  # נרצה לראות שה-good כן נקרא

# === TEST 6: Events Are Thread-Safe ===
def test_thread_safety():
    publisher = EventPublisher()
    results = []

    def cb(event): results.append(event.data["index"])

    publisher.subscribe(EventType.PAWN_PROMOTED, cb)

    import threading
    threads = [
        threading.Thread(target=publisher.publish, args=(EventType.PAWN_PROMOTED, {"index": i}))
        for i in range(20)
    ]

    for t in threads: t.start()
    for t in threads: t.join()

    assert sorted(results) == list(range(20))

# === TEST 7: Global Publisher Works ===
def test_global_publisher():
    results = []
    cb = create_callback(results, "global")

    event_publisher.subscribe(EventType.GAME_START, cb)
    event_publisher.publish(EventType.GAME_START, {"test": True})
    assert results[0][1].data["test"] is True
    event_publisher.unsubscribe(EventType.GAME_START, cb)

# === TEST 8: Publish Adds Timestamp Correctly ===
def test_timestamp_accuracy():
    publisher = EventPublisher()
    received = []

    def cb(event): received.append(event.timestamp)

    publisher.subscribe(EventType.MOVE_MADE, cb)
    now = int(time.time() * 1000)
    publisher.publish(EventType.MOVE_MADE)

    assert len(received) == 1
    assert abs(received[0] - now) < 500  # עד חצי שניה סטייה

# === TEST 9: Double Unsubscribe Does Nothing ===
def test_double_unsubscribe_does_not_crash():
    publisher = EventPublisher()
    cb = lambda e: None

    publisher.subscribe(EventType.GAME_END, cb)
    publisher.unsubscribe(EventType.GAME_END, cb)
    # שוב
    publisher.unsubscribe(EventType.GAME_END, cb)  # לא אמור לקרוס

# === TEST 10: Subscribe to Different Events ===
def test_subscribe_different_events():
    publisher = EventPublisher()
    events = []

    publisher.subscribe(EventType.GAME_START, create_callback(events, "start"))
    publisher.subscribe(EventType.GAME_END, create_callback(events, "end"))

    publisher.publish(EventType.GAME_END)
    publisher.publish(EventType.GAME_START)

    labels = [label for label, _ in events]
    assert "start" in labels
    assert "end" in labels
