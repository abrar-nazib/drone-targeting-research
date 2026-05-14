# Research Rationale

This research aims at creating a ROS environment to train a FPV drone to follow a target.
What needs to be done
- Install ROS 2 Jazzy (https://docs.ros.org/en/jazzy/) — installed in the usual location (`/opt/ros/jazzy`) so apt can resolve dependencies normally. **Project files (workspace, world assets, datasets, model checkpoints) live on the external SSD whenever possible — that is the priority for storage placement.**
- Install a suitable simulator that works with ROS. Good picture quality is needed
- Look for urban, car, human, road, houses as well as open terrain with trees, forest, mountains, roads, houses (need maybe two seperate worlds). Make sure the world assets look as picture perfect as possible.
- Create a dataset with segmented assets from stereo camera viewpoints from multiple positions
- Train a stereo vision model to do proper depth estimation on this as well as semantic segmentation