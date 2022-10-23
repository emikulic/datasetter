# autocaption
Automatic caption generation.

This is kept separate from datasetter so that you don't have to install a bunch
of machine learning libraries just to edit some captions.

## Install

```shell
virtualenv env           # Optional.
source env/bin/activate  # As above.
pip install torch        # Check https://pytorch.org/ for exact instructions.
pip install pillow timm fairscale
pip install transformers==4.15.0  # BLIP needs an older version.
cd datasetter/autocaption
git clone --depth=1 https://github.com/salesforce/BLIP
```

Oct 2022: I had to `sudo apt install rustc` to get `tokenizers==0.10.3` to install.

## Usage

GPU:

```shell
./autocaption.py ds.json
```

Force CPU:

```shell
env CUDA_VISIBLE_DEVICES= ./autocaption.py ds.json
```

This populates the `autocaption` field of each object in the dataset.
