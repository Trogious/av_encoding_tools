import DaVinciResolveScript as drs
import csv

names = []
csv_file = csv.reader(open("Davinvi4Noobs5.csv", "r"))
for row in csv_file:
    if "#" in row[0]:
        continue
    n = row[11]
    n = n[n.find("_")+1:]
    n = n[:n.find("-")]
    n = n.replace("_", " ")
    names.append(n)

resolve = drs.scriptapp("Resolve")
resolve.OpenPage("edit")
projectManager = resolve.GetProjectManager()
project = projectManager.GetCurrentProject()
if project.GetTimelineCount() > 0:
    i = 0
    timeline = project.GetCurrentTimeline()
    markers = timeline.GetMarkers()
    for frame_id in markers:
        marker = markers[frame_id]
        if marker["color"].lower() == "blue" and marker["name"].startswith("Marker"):
            timeline.DeleteMarkerAtFrame(frame_id)
            timeline.AddMarker(frame_id, "Red", names[i], "", 1)
        i += 1
