---
tags: meta
---
# Scheduler

Runs Lua functions on a schedule while SilverBullet is open, using its `cron:secondPassed` event. Jobs are checked once a minute.

```lua
scheduler.define {name = "Task sync", every = "15m", devices = {"desktop"}, run = function() ... end}
```

* `every` takes minutes, hours or days (`"15m"`, `"2h"`, `"1d"`).
* `devices` limits a job to devices with those names. Use `Scheduler: Name This Device` to set the name of the current client.
* A job returning `false` is tried again at the next check instead of waiting for its next run.
* Uses a [Web Lock](https://developer.mozilla.org/en-US/docs/Web/API/Web_Locks_API) per job to prevent multiple tabs/windows from running the same job.


## Implementation

```space-lua
-- priority: 20
scheduler = {jobs = {}}

local units = {m = 60, h = 3600, d = 86400}

function scheduler.define(job)
  local n, unit = (job.every or ""):match("^(%d+)([mhd])$")
  if not n then
    error("Scheduler job " .. job.name .. ": every should look like 15m, 2h or 1d")
  end
  job.seconds = tonumber(n) * units[unit]
  scheduler.jobs[job.name] = job
end

function scheduler.deviceName()
  return clientStore.get("scheduler.device")
end

local function runsHere(job)
  return not job.devices or table.includes(job.devices, scheduler.deviceName())
end

local function isDue(job, now)
  return now - (clientStore.get("scheduler.lastRun." .. job.name) or 0) >= job.seconds
end

local checking, lastCheck = false, 0

local function check()
  local now = os.time()
  local syncing = sync.isEnabled()
  if syncing and not sync.hasInitialSyncCompleted() then
    return
  end
  local due = {}
  for name, job in pairs(scheduler.jobs) do
    if runsHere(job) and isDue(job, now) then
      due[name] = job
    end
  end
  if not next(due) then
    return
  end
  if syncing and not pcall(sync.performSpaceSync) then
    return
  end
  for name, job in pairs(due) do
    -- Use a web lock to prevent multiple tabs/windows from all running the same jobs
    js.window.navigator.locks.request("scheduler:" .. name, {ifAvailable = true}, function(lock)
      if lock == nil or not isDue(job, now) then
        return
      end
      local ok, result = pcall(job.run)
      if ok then
        clientStore.set("scheduler.lastError." .. name, nil)
      else
        clientStore.set("scheduler.lastError." .. name, os.date("%Y-%m-%d %H:%M ") .. tostring(result))
        editor.flashNotification("Scheduler job " .. name .. " failed: " .. tostring(result), "error")
      end
      if result ~= false then
        clientStore.set("scheduler.lastRun." .. name, now)
      end
    end)
  end
end

event.listen {
  name = "cron:secondPassed",
  run = function()
    local now = os.time()
    if checking or now - lastCheck < 60 then
      return
    end
    checking, lastCheck = true, now
    local ok, err = pcall(check)
    checking = false
    if not ok then
      editor.flashNotification("Scheduler check failed: " .. tostring(err), "error")
    end
  end
}

command.define {
  name = "Scheduler: Name This Device",
  run = function()
    local name = editor.prompt("Name for this device", scheduler.deviceName() or "")
    if name then
      clientStore.set("scheduler.device", string.trim(name) ~= "" and string.trim(name) or nil)
    end
  end
}

local function when(t)
  return t and os.date("%Y-%m-%d %H:%M", t) or "–"
end

virtualPage.define {
  pattern = "scheduler:jobs",
  run = function()
    local names = {}
    for name in pairs(scheduler.jobs) do
      table.insert(names, name)
    end
    table.sort(names)
    local rows = {
      "This device: **" .. (scheduler.deviceName() or "unnamed") .. "** (name it with `Scheduler: Name This Device`)",
      "",
      "| Job | Schedule | Devices | Here | Last run | Next run | Last error |",
      "|---|---|---|---|---|---|---|",
    }
    for _, name in ipairs(names) do
      local job = scheduler.jobs[name]
      local here = runsHere(job)
      local last = clientStore.get("scheduler.lastRun." .. name)
      local nextRun = last and last + job.seconds or os.time()
      table.insert(rows, "| " .. table.concat({
        name, "every " .. job.every, job.devices and table.concat(job.devices, ", ") or "any",
        here and "yes" or "no", when(last), here and when(nextRun) or "–",
        ((clientStore.get("scheduler.lastError." .. name) or ""):gsub("|", "/")),
      }, " | ") .. " |")
    end
    return "# Scheduled jobs\n\n" .. table.concat(rows, "\n") .. "\n\nLast and next runs are for this device. Jobs are defined with `scheduler.define`, see [[Library/justyns/Scheduler]].\n"
  end
}

command.define {
  name = "Scheduler: Show Jobs",
  run = function()
    editor.navigate("scheduler:jobs")
  end
}
```