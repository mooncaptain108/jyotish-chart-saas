# Jyotish Query
## Data Storage

Jyotish Query starts with no data stored. At the very least you will have to enter in one location. From there click New to enter data to render a chart. Or click Muhurta to search for auspicious elective times.

All the data that is entered into Jyotish Query is stored locally in the browser cache. All the data generated in the Muhurta interface is also stored locally. As long as the cache is not cleared the data will be accessible.

Since the browser keeps the data in its cache the browser settings for cache management determine if the data is maintained between Jyotish Query use. The default behavior for browsers is to maintain cache between browser sessions.

To move data to another location and to prevent loss of data use the Export button found in Settings (click the Gear icon). From there you can restore the data or load the file using the Import button into another browser or copy it to another computer to be loaded there.

No data is stored on the server that is running Jyotish Query.

When importing with **Merge**:
- Charts you already have (same name, date, time and birthplace) are skipped, as are repeats within the file, so importing the same file twice does not create duplicates.
- Any chart whose location is not yet in your Atlas gets an Atlas entry created for it automatically, with its time zone looked up from the coordinates. If an existing Atlas location is within about 2 km, the chart is pointed at that one instead of adding a near-duplicate. A different place that happens to share a name with an existing entry is added with its coordinates in brackets after the name.
- Locations carried in the file are added to your Atlas, but never replace ones you already have.

A summary at the end shows how many charts were added, how many duplicates were skipped and how many Atlas locations were created.

**Backup reminder:** the opening screen shows a green line when charts or Atlas locations have been added, changed or deleted since your last full export (an export with every chart ticked), with the date of that export. It disappears after the next full export.
