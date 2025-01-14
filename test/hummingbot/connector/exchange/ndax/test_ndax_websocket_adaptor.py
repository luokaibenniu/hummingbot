import asyncio
import json
from unittest import TestCase
from unittest.mock import patch

from hummingbot.connector.exchange.ndax.ndax_websocket_adaptor import NdaxWebSocketAdaptor
from hummingbot.connector.exchange.ndax import ndax_constants as CONSTANTS
from hummingbot.core.api_throttler.async_throttler import AsyncThrottler
from test.hummingbot.connector.network_mocking_assistant import NetworkMockingAssistant


class NdaxWebSocketAdaptorTests(TestCase):

    def setUp(self) -> None:
        super().setUp()
        self.mocking_assistant = NetworkMockingAssistant()

    @patch("aiohttp.ClientSession.ws_connect")
    def test_sending_messages_increment_message_number(self, mock_ws):
        sent_messages = []
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()
        mock_ws.return_value.send_json.side_effect = lambda sent_message: sent_messages.append(sent_message)

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        payload = {}
        asyncio.get_event_loop().run_until_complete(adaptor.send_request(endpoint_name=CONSTANTS.WS_PING_REQUEST,
                                                                         payload=payload,
                                                                         limit_id=CONSTANTS.WS_PING_ID))
        asyncio.get_event_loop().run_until_complete(adaptor.send_request(endpoint_name=CONSTANTS.WS_PING_REQUEST,
                                                                         payload=payload,
                                                                         limit_id=CONSTANTS.WS_PING_ID))
        asyncio.get_event_loop().run_until_complete(adaptor.send_request(endpoint_name=CONSTANTS.WS_ORDER_BOOK_CHANNEL,
                                                                         payload=payload))
        self.assertEqual(3, len(sent_messages))

        message = sent_messages[0]
        self.assertEqual(1, message.get('i'))
        message = sent_messages[1]
        self.assertEqual(2, message.get('i'))
        message = sent_messages[2]
        self.assertEqual(3, message.get('i'))

    @patch("aiohttp.ClientSession.ws_connect")
    def test_request_message_structure(self, mock_ws):
        sent_messages = []
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()
        mock_ws.return_value.send_json.side_effect = lambda sent_message: sent_messages.append(sent_message)

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        payload = {"TestElement1": "Value1", "TestElement2": "Value2"}
        asyncio.get_event_loop().run_until_complete(adaptor.send_request(endpoint_name=CONSTANTS.WS_PING_REQUEST,
                                                                         payload=payload,
                                                                         limit_id=CONSTANTS.WS_PING_ID))

        self.assertEqual(1, len(sent_messages))
        message = sent_messages[0]

        self.assertEqual(0, message.get('m'))
        self.assertEqual(1, message.get('i'))
        self.assertEqual(CONSTANTS.WS_PING_REQUEST, message.get('n'))
        message_payload = json.loads(message.get('o'))
        self.assertEqual(payload, message_payload)

    @patch("aiohttp.ClientSession.ws_connect")
    def test_receive_message(self, mock_ws):
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()
        self.mocking_assistant.add_websocket_aiohttp_message(mock_ws.return_value, 'test message')

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        received_message = asyncio.get_event_loop().run_until_complete(adaptor.receive())

        self.assertEqual('test message', received_message.data)

    @patch("aiohttp.ClientSession.ws_connect")
    def test_close(self, mock_ws):
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        asyncio.get_event_loop().run_until_complete(adaptor.close())

        self.assertEquals(1, mock_ws.return_value.close.await_count)

    @patch("aiohttp.ClientSession.ws_connect")
    def test_get_payload_from_raw_received_message(self, mock_ws):
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()
        payload = {"Key1": True,
                   "Key2": "Value2"}
        message = {"m": 1,
                   "i": 1,
                   "n": "Endpoint",
                   "o": json.dumps(payload)}
        raw_message = json.dumps(message)

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        extracted_payload = adaptor.payload_from_raw_message(raw_message=raw_message)

        self.assertEqual(payload, extracted_payload)

    @patch("aiohttp.ClientSession.ws_connect")
    def test_get_endpoint_from_raw_received_message(self, mock_ws):
        throttler = AsyncThrottler(CONSTANTS.RATE_LIMITS)
        mock_ws.return_value = self.mocking_assistant.create_websocket_mock()
        payload = {"Key1": True,
                   "Key2": "Value2"}
        message = {"m": 1,
                   "i": 1,
                   "n": "Endpoint",
                   "o": json.dumps(payload)}
        raw_message = json.dumps(message)

        adaptor = NdaxWebSocketAdaptor(throttler, websocket=mock_ws.return_value)
        extracted_endpoint = adaptor.endpoint_from_raw_message(raw_message=raw_message)

        self.assertEqual("Endpoint", extracted_endpoint)
