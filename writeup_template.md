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

![alt text][image2]
### Autonomous Navigation and Mapping

I have tried to add comments into the code so that it could talk for itself. By running on the simulator with 1280x800/good resoloution I believe that i can achieve the goal of mapping 40% of the environment awith 60% of the fidelity. In fact most of the time I manage to explore 95%+ area and pick all the samples unless there is some really unfortunate stuck. However when the Rover continues to explore and the mapped area gets increased further the fidelity goes down and eventualy may fall below 50%. So the error of mapping increases the more Rover explores. One of the reasons for that probably not very smooth movements which doesn't produce right perception data ( explained below ).

In addtional to an ability of exploring and locating the samples Rover is capable of picking them up. For that *perception_step()* function has been modified so that (angle, distance) parameters it returns point towards the sample located rather than average angle of a navigatable area. I am using a threashold for the number of yellow-ish colors detected in the input image to avoid missinterpreting the other parts of the environment with the sample. Once the sample is detected the Rover moves into a special state called 'near_sample'. Not a very great name though, this  means that some sample is being observed by the Rover, not that the Rover is already close enough to pick it up. Once in this state the Rover reduces the spead and approaches the sample on a low speed to avoid an accidental moving into a direction where the sample will no longer be observable. Also to avoid loosing the truck of the sample I do enforce braking once the sample is located, however when the speed is too high braking appears to be quite hard and it drammatically cuts the % of a fidelity. Instead of this I am thinking it would be better to record the sample's position in the world coordinates and follow more smoother moving approach: reduce the throttling, gradually stop, turn around and pick the sampler. My temporaty solution to this problem is to reduce the ground speed value to 1.5 m/s from 2.0 m/s. 

The Rover may accidentaly drive into the area where steering posibilities are limitted and basically will stuck in there. *decision_step()* function has a very simplistic approach to address that. I am trying to tack a **stuck** state there. I do record how often Rover appears in position (x,y) having a minimum speed ( below 0.2 ). if Rover has been in (x,y) position for too long and not moving it is marked as being stuck. Once in a stuck state there is a pretty simple algorithm for the Rover to unstack itself: basically try to pull into all the direction periodically with the maximum throttle, i.e. all the combination of throttling (-1, 1) and steering (-15, 15). Once Rover gains some velocity (  +-0.2 ) it is no more considered as in stuck.
The stuck avoiding algorithm is conflicting with a slow motion apprach of samples picking, thus it is disabled when Rover is in 'near_sample' state. Which leads into a possibility for it to get stuck forever if Rover cannot come close enough to the sample to pick it up due to some reasons. It is a likely case because samples are usually located nearby the mountains and there might be difficulties with moving straight in that environment.

I have tried to address avoid visiting same areas again and again. If I knew where Rover have been most recently I can make a more complex decision regarding wher it should drive next rather than just taking a median from a navigatable area. in *decision_step* I do apply that logic. Basically to make a decision Rover considers 2 factors:  navigatable(terrain) nearby area and timestamps for the most recently visited points. Those points that have greater than 0 timestamp have alreay been explored and are being removed from the navigatable points set. This way the Rover has less and less chance to follow the same path many times.

I started with defining a 'visited map'. This is a (200,200) numpy array defined in world coordinates that records the last timestamp of visiting the position (x,y) on the map. The idea is to *encourage* the Rover to move away from the areas that have been visited recently in a favor of going to the not yet visited places. For that I take the recorded timestamps and find coordinates of the points that have values above zero. Then I transform those positions into the rover-centric coordinates by applying translation, rotation and scale to be compliant with how Rover sees the navigatable area , i.e. I define a **world_to_pix** function that allows to move a world point into the pixel space. Not very accurate but should work as a heuristic I think.  With this approach I can map 95-98% of the area, and collect all the samples. However it may take up to 10 minutes, because the Rover may still explores same areas multiple times before it moves to the new location.


![alt text][image3]


