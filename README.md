# datasetter
Tooling for building datasets.

Separate phase / tool for adding images, for security:

    ./add.py ds_name.json dir1 file1 file2... [--caption="optional default caption"]

Then run a webserver to be able to edit metadata:

    ./datasetter.py ds_name.json

Finally, a CLI to generate a dataset directory:

    ./prep.py --out=dataset/ ds1.json ds2.json ds3.json

Need to make this work incrementally at some point.

JSON looks like: text file with one line per data item:

```
{
 n: 1,                         # Unique ID for the data item, this is the primary key.
 fn: '/path/to/original.jpg',  # Absolute path to original file.
 md5: 'abcd...',               # MD5 of **original file**, not unique since one file can supply multiple crops.
 fsz: 123456,                  # Size of original file.
 orig_w, orig_h: int,          # Width and height of original file.
 x, y, w, h: int,              # Crop coords.
 rot: 0..3,                    # How many rot90s() should be applied after crop.
 caption: 'blah...',           # String caption.
 manual_ts: (int timestamp)    # Set to the time when this metadata was manually changed, otherwise absent.
 exclude: 'reason',            # If set, exclude from output dataset (for the given optional reason).
}
```

If a record with the same 'n' repeats, last wins.
This way, the dataset JSON can be updated by appending records.

# tests
To run tests, use

    python -m unittest discover
