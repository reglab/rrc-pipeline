# Racial Covenant Detection Pipeline

Authors: *Faiz Surani, Mirac Suzgun, Vyoma Raman, Christopher D. Manning, Peter Henderson, Daniel E. Ho.* Paper citation [below](#citation).

A pipeline for identifying racial covenants in property deeds. The pipeline processes images of property deeds through OCR and covenant detection models to identify discriminatory language.

## Requirements

- Docker
- For OCR and detection stages: NVIDIA GPU with minimum 16GB VRAM (recommended: NVIDIA L40S, A100, RTX 4090 or better)
- Docker NVIDIA runtime installed ([installation guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html))

The easiest way to run this pipeline is on a cloud GPU instance with pre-configured NVIDIA drivers/Docker runtime, such as AWS's NVIDIA-optimized Deep Learning AMIs on a g5.xlarge instance. However, you can run it on any hardware with appropriate GPU capability and system dependencies set up.

## Quick Start

1. Pull the latest image:
```bash
docker pull ghcr.io/reglab/rrc-pipeline:latest
```

2. Run the pipeline stages in sequence:

```bash
# Mount your image directory and output directory
# Note: directories must be absolute paths (i.e. beginning with /)
export RRC_IMAGE_DIR=/path/to/images
export RRC_DATA_DIR=/path/to/output

# 1. Ingest images
docker run --rm \
    -v $RRC_IMAGE_DIR:/data/images \
    -v $RRC_DATA_DIR:/data/output \
    ghcr.io/reglab/rrc-pipeline:latest rrc ingest

# 2. Run OCR
docker run --rm --gpus all \
    -v $RRC_IMAGE_DIR:/data/images \
    -v $RRC_DATA_DIR:/data/output \
    ghcr.io/reglab/rrc-pipeline:latest rrc ocr

# 3. Detect covenants
docker run --rm --gpus all \
    -v $RRC_IMAGE_DIR:/data/images \
    -v $RRC_DATA_DIR:/data/output \
    ghcr.io/reglab/rrc-pipeline:latest rrc detect

# 4. Export results
docker run --rm \
    -v $RRC_IMAGE_DIR:/data/images \
    -v $RRC_DATA_DIR:/data/output \
    ghcr.io/reglab/rrc-pipeline:latest rrc export
```

## Pipeline Stages

> [!NOTE]
> To see all available commands, run `docker run --rm ghcr.io/reglab/rrc-pipeline:latest rrc --help`.

### 1. Ingest (`rrc ingest`)
- Scans input directory for image files (jpg, jpeg, png, tiff, tif, bmp)
- Validates images can be opened
- Handles multi-page TIFF files
- Creates database records for new images

### 2. OCR (`rrc ocr`)
- Transcribes images using the DocTR OCR library
- Requires GPU acceleration
- Processes only images without existing transcriptions

### 3. Detection (`rrc detect`)
- Analyzes transcribed text using our Mistral-based covenant detection model
- Requires GPU acceleration
- Identifies presence of racial covenants and extracts relevant passages
- Processes only transcribed pages without existing predictions

### 4. Export (`rrc export`)
- Exports detection results to CSV format
- Includes confidence scores and extracted covenant text where found

### 5. Pipeline Summary (`rrc summarize`)
- Displays current pipeline progress and statistics
- Shows total page counts and processing status
- Reports covenant detection statistics

## Volume Mounts

The pipeline requires two volume mounts:

- `/data/images`: Directory containing input images
- `/data/output`: Directory for database, model weights, and output files

## Notes

- Supports common image formats including multi-page TIFFs
- Different pipeline stages can be run on different machines as long as the data and image directories are copied
- Each command supports `--help` for additional configuration options
- The pipeline currently only supports workflow starting from image scans---if you have pre-transcribed text and would find support for that useful, please [open an issue](https://github.com/reglab/rrc-pipeline/issues)

## Collaboration

For municipalities or states interested in running this pipeline at scale, we may be able to help. Please contact us at
```
reglab [at] law [dot] stanford [dot] edu
```

## Citation

If you use this pipeline for your research, we ask that you cite our paper as follows:
```
@article{suranisuzgun2024,
  title={AI for Scaling Legal Reform: Mapping and Redacting Racial Covenants in Santa Clara County},
  author={Surani, Faiz and Suzgun, Mirac and Raman, Vyoma and Manning, Christopher D. and Henderson, Peter and Ho, Daniel E.},
  url={https://dho.stanford.edu/wp-content/uploads/Covenants.pdf},
  year={2024}
}
```

## License

This project is licensed under the [MIT License](LICENSE).
