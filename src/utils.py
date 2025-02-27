import os, shutil, pickle
import torch, torchvision
import numpy as np 
from skimage import io as skio
from skimage import transform as sktransform
import argparse

#####################
#   Dataset Utils   #
#####################

def create_dogs_cats_dataset_atlas(image_directory, force=False):

    ''' Downloaded from https://www.kaggle.com/lingjin525/dogs-and-cats-fastai '''

    if 'dogscats' in os.listdir(image_directory):
        shutil.rmtree(os.path.join(image_directory,'dogscats'))
    if 'sample' in os.listdir(image_directory):
        shutil.rmtree(os.path.join(image_directory,'sample'))
    if 'test1' in os.listdir(image_directory):
        os.rename(os.path.join(image_directory,'test1'),os.path.join(image_directory,'test'))
    
    if not os.path.isfile(os.path.join(image_directory,'images_atlas.pkl')):

        image_paths = {}
        image_paths['train'] = \
            [os.path.join(image_directory,'train','cats',v) for v in os.listdir(os.path.join(image_directory,'train','cats'))] \
            + [os.path.join(image_directory,'train','dogs',v) for v in os.listdir(os.path.join(image_directory,'train','dogs'))]
        image_paths['validation'] = \
            [os.path.join(image_directory,'valid','cats',v) for v in os.listdir(os.path.join(image_directory,'valid','cats'))] \
            + [os.path.join(image_directory,'valid','dogs',v) for v in os.listdir(os.path.join(image_directory,'valid','dogs'))]
        with open(os.path.join(image_directory,'images_atlas.pkl'), 'wb') as file:
            pickle.dump(image_paths, file, pickle.HIGHEST_PROTOCOL)

def create_imagenet_dataset_atlas(image_directory):

    ''' Downloaded using https://github.com/mf1024/ImageNet-Datasets-Downloader with command:
            $ python3 downloader.py -data_root ../Datasets/imagenet -use_class_list True \
                -class_list n01484850, n02007558, n07753592, n07745940, n02051845, n02129604 \
                -images_per_class 2000
    '''

    if not os.path.isfile(os.path.join(image_directory,'images_atlas.pkl')):

        image_paths = {'train': list(), 'validation': list()}
        for class_name in os.listdir(image_directory):
            folder_name = os.path.join(image_directory,class_name)
            path_names = [os.path.join(folder_name,v) for v  in os.listdir(folder_name)]
            image_paths['train'] += path_names[:int(len(path_names)*0.85)]
            image_paths['validation'] += path_names[int(len(path_names)*0.85):]
        with open(os.path.join(image_directory,'images_atlas.pkl'), 'wb') as file:
            pickle.dump(image_paths, file, pickle.HIGHEST_PROTOCOL)
        
    if not os.path.isfile(os.path.join(image_directory,'name_to_label.pkl')):

        name_to_label = {'great white shark':0, 'flamingo':1, 'banana':2, 'strawberry':3, 'pelican':4, 'tiger':5}
        with open(os.path.join(image_directory,'name_to_label.pkl'), 'wb') as file:
            pickle.dump(name_to_label, file, pickle.HIGHEST_PROTOCOL)

    
class DogsCatsDataset(torch.utils.data.Dataset):

    def __init__(self, image_directory, input_size, train=True, transform=None, force=False):

        create_dogs_cats_dataset_atlas(image_directory)
        with open(os.path.join(image_directory,'images_atlas.pkl'), 'rb') as file:
            self.image_paths = pickle.load(file)['train'] if train else pickle.load(file)['validation']
        self.labels = [0 if v.split('/')[-1].split('.')[0] == 'cat' else 1 for v in self.image_paths]
        self.labels_name = ['cat', 'dog']
        self.input_size = input_size

    def __len__(self):

        return len(self.labels)
    
    def __getitem__(self, idx):

        image_path = self.image_paths[idx]
        image = skio.imread(image_path) 
        image = sktransform.resize(image, (self.input_size, self.input_size))
        image = np.swapaxes(np.swapaxes(image,0,2),1,2)
        label = self.labels[idx]
        return image, label

class SelectedImagenetDataset(torch.utils.data.Dataset):

    def __init__(self, image_directory, input_size, train=True, transform=None, force=False):

        create_imagenet_dataset_atlas(image_directory)
        with open(os.path.join(image_directory,'images_atlas.pkl'), 'rb') as file:
            self.image_paths = pickle.load(file)['train'] if train else pickle.load(file)['validation']
        with open(os.path.join(image_directory,'name_to_label.pkl'), 'rb') as file:
            name_to_label = pickle.load(file)
        
        self.labels = [name_to_label[v.split('/')[-2]] for v in self.image_paths]
        self.labels_name = ['great white shark', 'flamingo', 'banana', 'strawberry', 'pelican', 'tiger']
        self.input_size = input_size

    def __len__(self):

        return len(self.labels)
    
    def __getitem__(self, idx):

        image_path = self.image_paths[idx]
        image = skio.imread(image_path) 
        image = sktransform.resize(image, (self.input_size, self.input_size))
        if len(image.shape) != 3 or image.shape[2] == 1:
            image = image.reshape(self.input_size, self.input_size)
            image_new = np.empty((self.input_size, self.input_size, 3))
            image_new[:,:,0] = image / 0.3 
            image_new[:,:,1] = image / 0.59 
            image_new[:,:,2] = image / 0.11
            image = image_new
            
        image = np.swapaxes(np.swapaxes(image,0,2),1,2)
        label = self.labels[idx]
        return image, label

def get_dataset(dataset_name, dataset_path, input_size = 224, train = True):

    if dataset_name == 'dogscats':
        return DogsCatsDataset(dataset_path, input_size, train)
    elif dataset_name == 'imagenet':
        return SelectedImagenetDataset(dataset_path, input_size, train)

#####################
#   Parsing utils   #
#####################

def get_args_train():
    '''
    This function returns the arguments from terminal and set them to display
    ''' 

    parser = argparse.ArgumentParser(
        description = 'Adversarial attacks (training and evaluation) in Pytorch', 
        formatter_class= argparse.ArgumentDefaultsHelpFormatter
    )

    # Standard parsing
    parser.add_argument('--images_dir', default = '../Figures/',
        help = 'folder to store the resulting images')
    parser.add_argument('--models_dir', default = '../Models/',
        help = 'folder to store the models') 
    parser.add_argument('--datasets_dir', default = '../Datasets/',
        help = 'folder where the datasets are stored') 
    parser.add_argument('--dataset_name', choices = ['dogscats', 'imagenet'], default = 'imagenet', 
        help = 'dataset where to run the experiments') 
    parser.add_argument('--model_name', choices = [
            'images_shufflenetv2', 'images_mobilenetv2', 'images_resnet18'
        ], default= 'images_shufflenetv2',
        help = 'model used in the experiments')
    parser.add_argument('--n_iterations', type = int, default = 2000, 
        help = 'number of training iterations') 
    parser.add_argument('--batch_size', type = int, default = 32, 
        help = 'number of samples in each batch')
    parser.add_argument('--learning_rate', type = float, default = 0.03, 
        help = 'learning rate of the training algorithm (Adam)')
    parser.add_argument('--verbose_rate', type = int, default = 250, 
        help = 'number of iterations to show preliminar results and store the model')
    
    # Adversarial training parsing 
    parser.add_argument('--adversarial_training_algorithm', choices = [
            'none', 'FGSM_vanilla', 'PGD', 'FGSM', 'free'
        ], default = 'none',
        help = 'adversarial training algorithm for the experiments')
    parser.add_argument('--epsilon', type = float, default = 0.03, 
        help = 'strength of the linear perturbation of the adversarial')
    parser.add_argument('--min_value_input', type = float, default = 0.0, 
        help = 'minimum value of the input variable')
    parser.add_argument('--max_value_input', type = float, default = 1.0, 
        help = 'maximum value of the input variable')
    parser.add_argument('--n_steps_adv', type = int, default = 7, 
        help = 'number of steps for the iterative adversarial algorithms')

    return parser.parse_args()

def get_args_evaluate():
    '''
    This function returns the arguments from terminal and set them to display
    ''' 

    parser = argparse.ArgumentParser(
        description = 'Adversarial attacks (training and evaluation) in Pytorch', 
        formatter_class= argparse.ArgumentDefaultsHelpFormatter
    )

    # Standard parsing
    parser.add_argument('--images_dir', default = '../Figures/',
        help = 'folder to store the resulting images')
    parser.add_argument('--models_dir', default = '../Models/',
        help = 'folder to store the models') 
    parser.add_argument('--datasets_dir', default = '../Datasets/',
        help = 'folder where the datasets are stored') 
    parser.add_argument('--dataset_name', choices = ['dogscats', 'imagenet'], default = 'imagenet', 
        help = 'dataset where to run the experiments') 
    parser.add_argument('--model_name', choices = [
            'images_shufflenetv2', 'images_mobilenetv2', 'images_resnet18'
        ], default= 'images_shufflenetv2',
        help = 'model used in the experiments')
    parser.add_argument('--batch_size', type = int, default = 32, 
        help = 'number of samples in each batch')
    
    # Adversarial training parsing 
    parser.add_argument('--adversarial_training_algorithm', choices = [
            'none', 'FGSM', 'IFGSM', 'fast', 'free'
        ], default = 'none',
        help = 'adversarial training algorithm for the experiments')
    parser.add_argument('--adversarial_attack_algorithm', choices = [
            'none', 'FGSM', 'IFGSM', 'fast', 'free'
        ], default = 'FGSM',
        help = 'adversarial attack algorithm for the experiments')
    parser.add_argument('--epsilon', type = float, default = 0.03, 
        help = 'strength of the linear perturbation of the adversarial')
    parser.add_argument('--min_value_input', type = float, default = 0.0, 
        help = 'minimum value of the input variable')
    parser.add_argument('--max_value_input', type = float, default = 1.0, 
        help = 'maximum value of the input variable')
    parser.add_argument('--target', type=int, default=3,
        help = 'id of the target for the targeted attack')
    
    return parser.parse_args()



        
