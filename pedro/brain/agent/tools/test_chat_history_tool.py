import sys
import asyncio
from unittest.mock import MagicMock

# 1. Mock 'pedro.brain.modules.chat_history'
mock_chat_history_module = MagicMock()
sys.modules["pedro.brain.modules.chat_history"] = mock_chat_history_module

# 2. Mock 'pedro.utils.text_utils'
mock_text_utils = MagicMock()
# Define friendly_chat_log side effect or return value
def fake_friendly_log(messages):
    return "\n".join([f"{m.username}: {m.message}" for m in messages])
mock_text_utils.friendly_chat_log = fake_friendly_log
sys.modules["pedro.utils.text_utils"] = mock_text_utils

# 3. Mock 'pedro.brain.agent.tools.base'
mock_base = MagicMock()
class MockTool:
    pass
mock_base.Tool = MockTool
sys.modules["pedro.brain.agent.tools.base"] = mock_base

# 4. Now import the tool to test
# We need to make sure the import sees our mocks
from pedro.brain.agent.tools.chat_history_search import ChatHistorySearchTool

# Define a simple ChatLog class for testing since we can't import the real one (pydantic missing)
class ChatLog:
    def __init__(self, user_id, username, first_name, last_name, datetime, message):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.datetime = datetime
        self.message = message

async def test_chat_history_tool():
    print("Testing ChatHistorySearchTool...")
    
    # Mock ChatHistory
    mock_history = MagicMock()
    
    # Mock data
    mock_messages = {
        "2023-10-26": [
            ChatLog(user_id="1", username="user1", first_name="User", last_name="One", datetime="2023-10-26 10:00:00", message="Eu gosto de jogar Valorant"),
            ChatLog(user_id="2", username="user2", first_name="User", last_name="Two", datetime="2023-10-26 10:05:00", message="O Diogo estava jogando Zelda ontem"),
            ChatLog(user_id="1", username="user1", first_name="User", last_name="One", datetime="2023-10-26 10:10:00", message="Nada a ver, ele estava no CS"),
        ]
    }
    
    mock_history.get_messages.return_value = mock_messages
    
    # Initialize Tool
    chat_id = 12345
    tool = ChatHistorySearchTool(mock_history, chat_id)
    
    # Test 1: Search for "Zelda"
    print("\nTest 1: Search for 'Zelda'")
    result = await tool.execute(queries=["Zelda"])
    print(f"Result:\n{result}")
    assert "Zelda" in result
    assert "user2" in result
    
    # Test 2: Search for "CS"
    print("\nTest 2: Search for 'CS'")
    result = await tool.execute(queries=["CS"])
    print(f"Result:\n{result}")
    assert "CS" in result
    assert "user1" in result

    # Test 3: Search for non-existent term
    print("\nTest 3: Search for 'Fortnite'")
    result = await tool.execute(queries=["Fortnite"])
    print(f"Result:\n{result}")
    assert "Nenhuma mensagem encontrada" in result

    # Test 4: Verify chat_id was passed correctly to history
    mock_history.get_messages.assert_called_with(chat_id, days_limit=3)
    print("\nTest 4: Correct chat_id usage verified.")

    # Test 5: Multi-keyword search
    print("\nTest 5: Search for ['Zelda', 'CS']")
    result = await tool.execute(queries=["Zelda", "CS"])
    print(f"Result:\n{result}")
    assert "Zelda" in result
    assert "CS" in result
    
    # Test 6: Empty queries (retrieve all/recent)
    print("\nTest 6: Search with empty queries")
    result = await tool.execute(queries=[])
    print(f"Result (snippet):\n{result[:100]}...") 
    # Must contain everything available in the mock
    assert "Zelda" in result
    assert "CS" in result
    assert "Valorant" in result
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    asyncio.run(test_chat_history_tool())
