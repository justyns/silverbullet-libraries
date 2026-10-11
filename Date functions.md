
#meta

## Implementation

```space-lua
-- Define the function to get the current date and time
function getCurrentDateTime()
  local now = os.date("*t") -- Get the current date and time as a table
  local year = now.year
  local month = string.format("%02d", now.month)
  local day = string.format("%02d", now.day)
  local hours = string.format("%02d", now.hour)
  local minutes = string.format("%02d", now.min)

  return string.format("%d-%s-%s %s:%s", year, month, day, hours, minutes)
end

function getToday()
  local now = os.date("*t") -- Get the current date and time as a table
  local year = now.year
  local month = string.format("%02d", now.month)
  local day = string.format("%02d", now.day)
  local hours = string.format("%02d", now.hour)
  local minutes = string.format("%02d", now.min)

  return string.format("%d-%s-%s", year, month, day)
end

-- Define the slash command for /now
slashCommand.define {
  name = "now",
  run = function()
    local dateTime = getCurrentDateTime()
    editor.insertAtCursor(dateTime, false, true)
  end
}

-- Define the slash command for /currentDateTime
slashCommand.define {
  name = "currentDateTime",
  run = function()
    local dateTime = getCurrentDateTime()
    editor.insertAtCursor(dateTime, false, true)
  end
}
```
