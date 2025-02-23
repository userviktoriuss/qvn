import sys as _s

import subprocess
import glob
import cv2
import os
import numpy as np
import random
import shutil

def convertFPS(input_file,fps,output_file):

    parameters = {}
    parameters["input_file"] = input_file
    parameters["filter"] = "fps=" + str(fps)
    parameters["output_file"] = output_file

    commands_list = [
        "ffmpeg",
        "-i",
        parameters["input_file"],
        "-filter:v",
        parameters["filter"],
        parameters["output_file"]
        ]

    return commands_list

def extractFrames(input_file, frames_directory):
    parameters = {}
    parameters["rate_1"] = "1"
    parameters["input_file"] = input_file
    parameters["rate_2"] = "1"
    parameters["output_file"] = os.join(frames_directory, "%04d.jpg")

    commands_list = [
        "ffmpeg",
        "-r",
        parameters["rate_1"],
        "-i",
        parameters["input_file"],
        "-r",
        parameters["rate_2"],
        parameters["output_file"]
        ]

    return commands_list

def apply_noise(noise_type,image):
    if noise_type == "saltpepper":
        prob = 0.1
        output = np.zeros(image.shape,np.uint8)
        thres = 1 - prob 
        for i in range(image.shape[0]):
            for j in range(image.shape[1]):
                rdn = random.random()
                if rdn < prob:
                    output[i][j] = 0
                elif rdn > thres:
                    output[i][j] = 255
                else:
                    output[i][j] = image[i][j]
        return output
    elif noise_type =="speckle":
        row,col,ch = image.shape
        gauss = np.random.randn(row,col,ch)
        gauss = gauss.reshape(row,col,ch)        
        noisy = image + image * gauss
        return noisy

def join_frames_to_video(input_files,output_directory,file_name_without_ext):
    parameters = {}
    parameters["framerate"] = "24"
    parameters["input_files"] = input_files
    parameters["video_codec"] = "libx264"
    parameters["output_rate"] = "24"
    parameters["pixel_format"] = "yuv420p"
    parameters["output_file"] = os.join(output_directory, file_name_without_ext + "_noise_noaudio.mp4")

    commands_list = [
        "ffmpeg",
        "-framerate",
        parameters["framerate"],
        "-i",
        parameters["input_files"],
        "-c:v",
        parameters["video_codec"],
        "-r",
        parameters["output_rate"],
        "-pix_fmt",
        parameters["pixel_format"],
        parameters["output_file"]
        ]

    return commands_list

def run(video_file,noise_type):
    owd = os.getcwd()

    current_video_dir = os.path.dirname(video_file)
    input_filename = os.path.basename(video_file)
    input_filename_without_ext = os.path.splitext(input_filename)[0]
    new_working_dir = os.join(current_video_dir, input_filename_without_ext)
    os.mkdir(new_working_dir)
    os.chdir(new_working_dir)

    base_file = "24fps.mp4"
    subprocess.run(convertFPS(video_file,24,base_file))

    frames_directory = os.join(new_working_dir, "frames")
    os.mkdir(frames_directory)
    subprocess.run(extractFrames(base_file, frames_directory))

    altered_frames_directory = os.join(new_working_dir, "altered_frames")
    os.mkdir(altered_frames_directory)

    print('Processing frames...')

    for img_file in glob.glob(os.join(frames_directory, "*.jpg")):
        file_name = os.path.basename(img_file)
        file_name_without_ext = os.path.splitext(file_name)[0]

        img = cv2.imread(img_file, flags=cv2.IMREAD_COLOR)

        new_img = apply_noise(noise_type,img)
        
        new_file_name = os.join(altered_frames_directory, file_name_without_ext + '.jpg')
        cv2.imwrite(new_file_name, new_img)

    subprocess.run(join_frames_to_video(os.join(altered_frames_directory, "%04d.jpg"), current_video_dir, input_filename_without_ext))

    shutil.rmtree(new_working_dir, ignore_errors=True)

    os.chdir(current_video_dir)
    os.rmdir(new_working_dir)

    subprocess.run("ffmpeg -i " + input_filename_without_ext + ".mp4 -vn " + input_filename_without_ext + ".mp3")
    subprocess.run("ffmpeg -i " + input_filename_without_ext + "_noise_noaudio.mp4 -i " + input_filename_without_ext + ".mp3 -c:v copy -map 0:v -map 1:a -y " + input_filename_without_ext + "_noisy.mp4 ")

    os.remove(input_filename_without_ext + "_noise_noaudio.mp4")
    os.remove(input_filename_without_ext + ".mp3")    


if __name__ == "__main__":
    video_file = _s.argv[1]
    noise_type = 'speckle'

    if len(_s.argv) == 3:
        noise_type = _s.argv[2]
    
    run(video_file,noise_type)
