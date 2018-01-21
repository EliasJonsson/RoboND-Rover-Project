## Project: Search and Sample Return
### Author:Elias Jonsson

---
### Solution
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.

Following is the function that I used to find which pixels of the warped image belong to rock samples:

```python
def find_rocks(img, rgb_thresh=(110, 110, 50)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] < rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select
```

As we can see from the method, the condition we use to determine if a pixel belongs to a rock or not is the RGB values of the warped image. The conditions that we used were that a pixel belongs to a rock sample if it is high in red and green and low in blue. Examples of the usage of this method can be seen below, both an image sampled from the original test set and from the recorded data.

**Test image**: threshed image of a rock: 
![alt text](https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/writeup_images/test_rocks.png)

**Recorded image**: threshed image of a rock: 
![alt text](https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/writeup_images/recorded_rock.png)

To find the obstacle terrain I used the following code:

```python
# Obstacle terrain
camera_view_mask = perspect_transform(np.ones_like(grid_img[:,:,0]), source, destination)
threshed_obstacles = -camera_view_mask * (threshed - 1)
```

So what this code does is that it converts all pixels inside of the camera view that has value `1` in `threshed` to `0` and all pixels that have value `0` to `1`. Therefore, `-(threshed - 1)` swaps the pixel values and `camera_view_mask` guarantees that the pixels outside of the camera view are not considered as obstacles. Examples of the usage of this code can be seen below, both an image sampled from the original test set and from the recorded data.

**Test image**: threshed image of an obstacle: 
![alt text](https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/writeup_images/test_obstacles.png)

**Recorded image**: threshed image of an obstacle:
![alt text](https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/writeup_images/recorded_obstacles.png)


#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 

For this part, I didn't do anything out of the ordinary. Except, I solved the problem of some pixels belonging both to obstacles and navigable terrain with the simple criteria; if a pixel has been classified more often as an obstacle than a navigable terrain, then it is an obstacle otherwise a navigable terrain. The obstacle and the rocks are found with the code explained above. And then just transformed to world pixels. I chose red as the color to denote obstacles, blue for navigable terrain, green for the ground truth and white for rocks. The video created can be found at the link below.

<https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/output/test_mapping.mp4>
### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.

The `perception_step()` is very similar to the notebook version of `process_image()`. However, the main difference is that now we don't really solve the problem of some pixels classified as both obstacles and a navigable terrain. Now we just assume that a pixel can be both. Visually we will though see a pixel that has been classified more often as an obstacle as an obstacle and a pixel that has been classified more often as a navigable terrain as a navigable terrain. Just because we will increase the color tone of the obstacle every time we classify the pixel as an obstacle and the same for the navigable terrain. However, this can cause low fidelity score, because the fidelity score only considers if a pixel has ever been classified as a navigable terrain or not.

Another thing that I changed was that I will not make any classifications of pixels when the rover is breaking or driving very slowly. The reason for this is when the rover slows down very quickly or collides with an obstacle. The rover's camera often points out to the sky or to the road and will consider almost all pixels as navigable terrain which maps very badly to world coordinates and a significant decrease in the fidelity score.

For the `decision.py` I changed very little. I only added the functionality to collect rocks. So if the rover sees a rock, he will stop and turn towards the rock. Drive slowly towards the rock, pick it up and go back to `forward` mode. To do that I changed the Rover class a bit in `drive_rover.py`. I added the angle and the distance to the rock as attributes in the `Rover` class.

#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  


**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

For this part, I used screen resolution 1024x768 and Graphic Quality good. When I ran the `drive_rover.py` the FPS output to terminal varied from 6 to 30.

Following is an image of a time when I beat the benchmark.

![alt text](https://github.com/EliasJonsson/RoboND-Rover-Project/blob/master/writeup_images/benchmark.png)

The main problem with my implementation right now is low fidelity score. So what I could do to change that is 
* Solving the problem of a pixel being classified as both an obstacle and a navigable terrain in a smarter way. At least so that a pixel that has been classified a lot more often as an obstacle will not be considered as a navigable terrain.
* A smarter algorithm to determine if a pixel is a navigable terrain or not.


Another problem is that the ending result is quite depending on the starting point. But if the rover starts going to one half of the map he will stick there for a very long time.
* What I could do here is to add some randomness in the decision making when choosing the navigable angle. The probabilities would be depending on the likelihood of the angle to be a navigable terrain. By doing that, the path that the rover takes will not at least be 100% deterministic. But I could see the rover being very unstable though, and do weird things.


The last major problem is that the rover sometimes gets stuck. Either in a place surrounded by obstacles or finds the best navigable angle always to be left or right so he just drives in circles. One solution to this would be to track if the rover has been stopped or doing the same thing for a while and then make some action to get it out of it. However, that solution might involve annoyingly many `if` and `else` statements.

The best solution for all the problems above might though just be to implement some kind of machine learning, I could see reinforcement learning be an interesting tool here.


