# Xwh_BPY_Toolbox
A personal collection of Blender scripts I made. I decided to turn it into an addon to centralize my workflow.  
Feel free to use what fits your workflow.  

## Installation
* Zip the `Xwh_Toolbox` folder and drag it into Blender to install the whole addon.  
* Optionally, single file tools work on their own, and can be enabled by running them from the Text Editor tab.


## Fix Camera Jumps
A tool to fix instant teleports turning into sweeps when an animation is scaled from 30fps to 60fps.  

Works by analyzing rate of change of a curve to detect sweeping jumps, and moves deviating keyframes together to mitigate them.

Mainly made for Blender cameras, but works with other objects and with Auth3D cameras.

## Renamer
Renames objects, bones, or shape keys based on a CSV table or a Noesis dict (`.morph` & `.bone`). Can also export the current namings.

---  
#### Made by Hans Xwh  
:p
