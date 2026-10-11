---
tags: meta
---
# Recurring Tasks

Stamps `✅ YYYY-MM-DD` on tasks when you mark them as done, and adds the next occurrence of tasks with a `🔁` rule above the completed one. Uses the [Obsidian Tasks](https://publish.obsidian.md/tasks/) emoji format:

```
* [ ] Pay the electric bill 📅 2026-10-17 🔁 every month
* [ ] Change the furnace filter 📅 2026-10-05 🔁 every 90 days when done
```

* `every day|week|month|year` or `every N days|weeks|months|years` repeats from the `📅` date, keeping a fixed schedule even when you finish late.
* Adding `when done` (or writing `after N days`) repeats from the day you check it off.
* Month and year steps keep the day of the month, clamped to the month's last day.
* Checking a task from a query result or widget does not stamp or repeat it.

## Implementation

```space-lua
recurringTasks = {}

local datePattern = "%d%d%d%d%-%d%d%-%d%d"

local function parseDate(date)
  local y, m, d = date:match("^(%d%d%d%d)-(%d%d)-(%d%d)$")
  return tonumber(y), tonumber(m), tonumber(d)
end

local function daysInMonth(y, m)
  return os.date("*t", os.time({year = m == 12 and y + 1 or y, month = m % 12 + 1, day = 1, hour = 12}) - 86400).day
end

local function addMonths(date, n)
  local y, m, d = parseDate(date)
  local months = y * 12 + (m - 1) + n
  y, m = months // 12, months % 12 + 1
  return string.format("%04d-%02d-%02d", y, m, math.min(d, daysInMonth(y, m)))
end

local function addDays(date, n)
  local y, m, d = parseDate(date)
  return os.date("%Y-%m-%d", os.time({year = y, month = m, day = d, hour = 12}) + n * 86400)
end

-- The next date for a rule such as "every month" or "every 30 days when done", or nil if the rule is not understood.
function recurringTasks.nextDate(due, rule, today)
  rule = string.trim(rule:lower())
  local base = due
  local count, unit = rule:match("^every%s*(%d*)%s*(%a+)$")
  if not unit then
    count, unit = rule:match("^every%s*(%d*)%s*(%a+)%s+when%s+done$")
    if not unit then
      count, unit = rule:match("^after%s*(%d*)%s*(%a+)$")
    end
    base = today
  end
  if not unit then
    return nil
  end
  local n = tonumber(count) or 1
  unit = unit:gsub("s$", "")
  if unit == "day" then
    return addDays(base, n)
  elseif unit == "week" then
    return addDays(base, 7 * n)
  elseif unit == "month" then
    return addMonths(base, n)
  elseif unit == "year" then
    return addMonths(base, 12 * n)
  end
end

-- For a task's text (from its checkbox on) just after it was checked, returns the
-- stamped text and, for a recurring task, the text of its next occurrence (or nil).
function recurringTasks.complete(taskText, today)
  local stamped = string.trimEnd(taskText) .. " ✅ " .. today
  local rule = taskText:match("🔁%s*([%w ]+)")
  local due = taskText:match("📅%s*(" .. datePattern .. ")")
  if not (rule and due) then
    return stamped, nil
  end
  local nextDue = recurringTasks.nextDate(due, rule, today)
  if not nextDue then
    error("Unknown recurrence rule: " .. rule)
  end
  local nextText = taskText:gsub("^%[.%]", "[ ]", 1)
  nextText = nextText:gsub("📅%s*" .. datePattern, "📅 " .. nextDue, 1)
  return stamped, nextText
end

function recurringTasks.uncomplete(taskText)
  return (taskText:gsub("%s*✅%s*" .. datePattern, ""))
end

event.listen {
  name = "task:stateChange",
  run = function(e)
    local d = e.data
    if not d.text then
      return
    end
    local text = editor.getText()
    local taskText = text:sub(d.from + 1, d.to)
    if d.newState == "x" or d.newState == "X" then
      local stamped, nextText = recurringTasks.complete(taskText, os.date("%Y-%m-%d"))
      local changes = {{from = d.from, to = d.to, insert = stamped}}
      if nextText then
        local lineStart = d.from
        while lineStart > 0 and text:sub(lineStart, lineStart) ~= "\n" do
          lineStart = lineStart - 1
        end
        local prefix = text:sub(lineStart + 1, d.from)
        table.insert(changes, 1, {from = lineStart, insert = prefix .. nextText .. "\n"})
      end
      editor.dispatch({changes = changes})
    elseif d.newState == " " then
      editor.dispatch({changes = {from = d.from, to = d.to, insert = recurringTasks.uncomplete(taskText)}})
    end
  end
}
```
