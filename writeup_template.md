## Project: Search and Sample Return
### Writeup Template: You can use this file as a template for your writeup if you want to submit it as a markdown file, but feel free to use some other method and submit a pdf if you prefer.

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[image1]: ./misc/rover_image.jpg
[image2]: ./calibration_images/example_grid1.jpg
[image3]: ./calibration_images/example_rock1.jpg 

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it!

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.
Here is an example of how to include an image in your writeup.

![alt text][image1]

#### 1. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 
And another! 

![alt text][image2]
### Autonomous Navigation and Mapping

I have tried to add comments into the code so that it could talk for itself. By running on the simulator with 1280x800 resoloution I believe that i can achieve the goal of mapping 40% of the environment awith 60% of the fidelity. However when the Rover continues to explore and the mapped area gets increased further the fidelity goes down and eventualy may fall below 50%. So the error of mapping increases the more Rover explores. Probably my threshold for terrain/obstacles/samples are not very accurate.

In addtional to an ability of exploring and locating the samples Rover is capable of picking them up. For that *perception_step()* function has been modified so that (angle, distance) parameters it returns point towards the sample located rather than average angle of a navigatable area. I am using a threashold for the number of yellow-ish colors detected in the input image to avoid missinterpreting the other parts of the environment with the sample. Once the sample is detected the Rover moves into a special state called 'near_sample'. Not a very great name though, this  means that some sample is being observed by the Rover, not that the Rover is already close enough to pick it up. Once in this state the Rover reduces the spead and approaches the sample with a minimum throttling to avoid an accidental moving into a direction where the sample will no longer be observable.  However if that happens the Rover will no longer be searching for the sample but rather will move back into the 'forward' state. 

The Rover may accidentaly drive into the area where steering posibilities are limitted and basically will stuck in there. *decision_step()* function has a very simplistic approach to address that. I am trying to tack a **stuck** state there. I do record how often Rover appears in position (x,y) having a minimum speed ( below 0.2 ). if Rover has been in (x,y) position for too long and not moving it is marked as being stuck. Once in a stuck state there is a pretty simple algorithm for the Rover to unstack itself: basically try to pull into all the direction periodically with the maximum throttle, i.e. all the combination of throttling (-1, 1) and steering (-15, 15). Once Rover gains some velocity (  +-0.2 ) it is no more considered as in stuck.
The stuck avoiding algorithm is conflicting with a slow motion apprach of samples picking, thus it is disabled when Rover is in 'near_sample' state. Which leads into a possibility for it to get stuck forever if Rover cannot come close enough to the sample to pick it up due to some reasons. It is a likely case because samples are usually located nearby the mountains and there might be difficulties with moving straight in that environment.

I have tried to address avoid visiting same areas again and again. If I knew where Rover have been most recently I can make a more complex decision regarding wher it should drive next rather than just taking a median from a navigatable area. in *decision_step* I do apply that logic. Basically to make a decision Rover considers 2 factors: (angles, distances) to navigatable(terrain) nearby area and (angles,distances) to the most recently visited points. I take a sum of mean values of those vectors where *the most recent visits* vectors I am using with a negative sign ( since we need to move away from the most recently visited points ). And then I clamp the result angle against the min/max angles of the visible navigatable area ( since Rover can move only by the road ) and choose it as a steering angle for Rover.    

I started with defining a 'visited map'. This is a (200,200) numpy array defined in world coordinates that records the last timestamp of visiting the position (x,y) on the map. The idea is to *encourage* the Rover to move away from the areas that have been visited recently in a favor of going to the not visited places or the places that have not been visited long enough. For that I take  mean value of the recorded timestamps and find coordinates of the points that have values above that mean value. Then I transform those positions into the rover-centric coordinates by applying translation, rotation and scale to be compliant with how Rover sees the navigatable area , i.e. I define a **world_to_pix** function that allows to move the world point into the pixel space. **world_to_pix** should *spread* the timestamp of 1 point in the world space on 10x10 region in the pixel space. Not very accurate but should work as a heuristics I think. **In anyways this part is not really working and needs to be debugged further.**


![alt text][image3]


