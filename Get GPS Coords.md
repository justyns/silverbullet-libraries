---
name: Library/justyns/Get GPS Coords
tags: meta/library
---

I'm using this in [[Library/Core/Quick Notes]] for the template when a new note is created. It works on desktop and mobile.

```space-lua
function getGpsCoords()
  return js.new(js.window.Promise, function(resolve, reject)
    js.window.navigator.geolocation.getCurrentPosition(
      function(position)
        local latitude = position.coords.latitude
        local longitude = position.coords.longitude
        editor.flashNotification("GPS: " .. latitude .. ", " .. longitude)
        resolve(latitude .. ", " .. longitude)
      end,
      function(err)
        js.log("Geolocation error:", err)
        reject(err)
      end
    )
  end)
end

command.define {
  name = "Get GPS Coords",
  run = getGpsCoords()
}
```
