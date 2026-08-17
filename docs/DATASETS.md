# Recommended Datasets (Reference for Milestone 2+)

These are referenced now (per the project spec's Milestone 1 task "Collect
sports biomechanics datasets") and will actually be downloaded/used starting
Milestone 2 when the pose estimation engine is built.

| Dataset | Purpose | Link |
|---|---|---|
| **Human3.6M** | Human pose estimation, joint tracking, movement analysis | http://vision.imar.ro/human3.6m/ |
| **MPII Human Pose** | Body keypoint detection, activity recognition | http://human-pose.mpi-inf.mpg.de/ |
| **COCO Keypoints** | Pose estimation training, human motion analysis | https://cocodataset.org/#keypoints-2020 |
| **SportsPose** | Sports-specific movement analysis, athlete posture assessment | https://sportspose.compute.dtu.dk/ |
| **FIFA Injury Dataset** (reference) | Injury trend analysis, risk factor modeling | Referenced via FIFA/UEFA injury studies — used as a reference model rather than a raw downloadable dataset |

## Why these matter for the platform

- **Human3.6M / MPII / COCO** are general-purpose human pose datasets used to
  train or fine-tune the pose estimation models (MediaPipe Pose / OpenPose /
  MoveNet / Detectron2) that will power the Pose Estimation Engine in
  Milestone 2.
- **SportsPose** is sport-specific, so it's the closest match for training
  models that need to recognize sport-specific movements (sprinting,
  jumping, cutting, throwing) rather than generic poses.
- **FIFA Injury Dataset** informs the *weighting* of the Injury Risk Scoring
  model (e.g. how much biomechanical deviation vs. training load vs. injury
  history should count toward risk) rather than being fed directly into pose
  estimation.

No dataset needs to be downloaded for Milestone 1 — this document simply
satisfies the "datasets collected/referenced" checklist item ahead of
building the actual pose estimation pipeline.
