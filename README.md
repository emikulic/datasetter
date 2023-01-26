# datasetter

Tooling for building datasets.

## Pipeline

First, use a separate tool for adding images. For security, the web UI can't
add or change filenames. Inputs have to be relative to the dataset dir that
contains the JSON file, although symlinks are allowed.

```shell
cd dataset/
~/datasetter/add.py ds_name.json dir1 file1 file2... [--caption="optional default caption"]
```

Then run a webserver to edit metadata:

```shell
~/datasetter/datasetter.py ds_name.json
```

Finally, a CLI to generate an output directory:

```shell
~/datasetter/prep.py outdir ds_name.json ds2.json ds3.json
```

Need to make this work incrementally at some point.

## Schema

JSON looks like: text file with one line per data item:

```
{
 n: 0,                         # Unique ID for the data item, this is the primary key.
 fn: 'path/to/original.jpg',   # Relative path to original file.
 md5: 'abcd...',               # MD5 of **original file**, not unique since one file can supply multiple crops.
 fsz: 123456,                  # Size of original file.
 orig_w, orig_h: int,          # Width and height of original file.
 x, y, w, h: int,              # Crop coords.
 rot: 0..3,                    # How many 90deg CCW rotations should be applied after crop.
 caption: 'blah...',           # String caption.
 manual_crop: 1 or absent,     # If 1, crop coords were set manually.
 manual_rot: 1 or absent,      # If 1, rotation was set manually.
 manual_ts: (int timestamp),   # Set to the time when this metadata was manually changed, otherwise absent.
 skip: 'reason',               # If set, exclude from output dataset for the given reason.
}
```

If a record with the same 'n' repeats, last wins.
This way, the dataset JSON can be updated by appending records.

## Tests

To run tests, use

```shell
python -m unittest discover
```
