<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>
<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->



<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->



<!-- PROJECT LOGO -->
<br />

<h3 align="center">Unsupervised learning reveals interpretable latent representations for translucency perception</h3>

  <p align="center">
    Chenxi Liao, Masataka Sawayama, Bei Xiao
  </p>

</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#data">Psychophysical experiment data</a></li>
        <li><a href="#analysis">Notebooks</a></li>
      </ul>
    </li>
   <!--  <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li> -->
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
<div align="center">
  <h1>Overview</h1>
</div>
  

<div align="center">
  <img src="images/intro.jpg" alt="Intro" width="677" height="408">
</div>

*Abstract:* Humans constantly assess the appearance of materials to plan actions, such as stepping on icy roads without slipping. Visual inference of materials is important but challenging because a given material can appear dramatically different in various scenes. This problem especially stands out for translucent materials, whose appearance strongly depends on lighting, geometry, and viewpoint. Despite this, humans can still distinguish between different materials, and it remains unsolved how to systematically discover visual features pertinent to material inference from natural images. Here, we develop an unsupervised style-based image generation model to identify perceptually relevant dimensions for translucent material appearances from photographs. We find our model, with its layer-wise latent representation, can synthesize images of diverse and realistic materials. Importantly, without supervision, human-understandable scene attributes, including object’s shape, material, and body color, spontaneously emerge in the model’s layer-wise latent space in a scale-specific manner. By embedding an image into the learned latent space, we can manipulate specific layers’ latent code to modify the appearance of the object in the image. Specifically, we find that manipulation on the early-layers (coarse spatial scale) transforms the object’s shape, while manipulation on the later-layers (fine spatial scale) modifies its body color. The middle-layers of the latent space selectively encode translucency features and manipulation on such layers coherently modifies the translucency appearance, without changing the object's shape or body color. Moreover, we find the middle-layers of the latent space can successfully predict human translucency ratings, suggesting that translucent impressions are established in mid-to-low spatial scale features. This layer-wise latent representation allows us to systematically discover perceptually relevant image features for human translucency perception. Together, our findings reveal that learning the scale-specific statistical structure of natural images might be crucial for humans to efficiently represent material properties across contexts.



<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Psychophysical experiment data

* Experiment 1: [Real-vs-generated discrimination](/data-analysis/data/Experiment1)
* Experiment 2: [Material attribute rating](/data-analysis/data/Experiment2)
* Experiment 3: [Perceptual evaluation of emerged scene attributes](/data-analysis/data/Experiment3)

## Model
* Please first download the pretrained TAG model from [Figshare](https://figshare.com/articles/dataset/Unsupervised_learning_reveals_interpretable_latent_representations_for_translucency_perception/21905463/1?file=38857887)
* Place the downloaded folder "Trained_TAG_Model" in the project's directory.
* You also need the StyleGAN model. Please clone the following repository to your working directory:
``` 
!git clone https://github.com/NVlabs/stylegan3.git
```

* To run the pretrained pixel2style2pixel model, please set up the `pixel2style2pixel/configs/paths_config.py` and define:
``` 
dataset_paths = {
    'soap_train':'/content/drive/MyDrive/soap_size1024_8k_train_test/soap_train_test8k/train_soap', ## Please change the path to the dataset
    'soap_test':'/content/drive/MyDrive/soap_size1024_8k_train_test/soap_train_test8k/test_soap'    ## Please change the path to the dataset
}
```
* To encode a real photograph into the latent space, you can use `pixel2style2pixel/scripts/inference.py` file. You can use the argument `save_latent_type` to embed the image in either W (`W`) or W+ (`Wplus_all`) space, and save the latent codes to a `.npy` file. Here is an example: 
``` 
python pixel2style2pixel/scripts/inference.py \
--exp_dir=path/to/export_the_saving \  ## need to change to your checkpoint path
--checkpoint_path=/path/to/pSp-encoder-soap-Wplus.pt \  ## need to change to the pSp encoder checkpoint path
--data_path=/path/to/folder_of_photo_to_encode \ ## need to change to your image folder (images you want to encode) path
--test_batch_size=5 \
--test_workers=4 \
--save_latent_type=Wplus_all \  ## accept "Wplus_all", "W", "Wplus_one_layer". if "Wplus_one_layer" is used, please also use an additional argument "save_latent_layer" to indicate which layer of W+ to save.
--couple_outputs
```

You can also load the W+ extracted from the 500 milky and 500 glycerin soap from this [ folder](/milky-glycerin-soaps-W-plus-code/500_milky_soap_Wplus_all_layers.npy).

* To train the encoder starting from a checkpoint:
``` 
!python scripts/train.py \
--dataset_type=soap_encode \
--exp_dir= path/to/export_the_saving \ ## need to change to your saving directory path
--output_size=1024 \
--workers=8 \
--batch_size=4 \
--test_batch_size=4 \
--test_workers=8 \
--val_interval=2500 \
--save_interval=10000 \
--encoder_type=GradualStyleEncoder \
--start_from_latent_avg \
--lpips_lambda=0.8 \
--l2_lambda=1 \
--id_lambda=0 \
--w_norm_lambda=0.005 \
--checkpoint_path=path/to/checkpoints/best_model.pt ## need to change to your checkpoint path
```

Please also check out the original [pixel2style2pixel](https://github.com/eladrich/pixel2style2pixel) repository to see more implementation details. 

* [TAG model](/data-analysis/TAG_playground.ipynb) illustrates the use of StyleGAN and the pixel2style2pixel encoder.


## Notebooks

The following notebooks can be used to replicate the figures in the manuscript:

* [Experiment 1 analysis](/data-analysis/Analysis-real-vs-generated-discrimination.ipynb)
* [Experiment 2 analysis](/data-analysis/Analysis-material-attribute-rating.ipynb)
* [Experiment 3 analysis](/data-analysis/Analysis-scene-attribute-evaluation.ipynb)
* [Experiment 3 analysis with Bayesian model](/data-analysis/MLM-analysis/MLM-semantics_brms_version.Rmd)
* [Independent Component Analysis of intermediate generative results of StyleGAN](/data-analysis/ICA-Middle-layer.ipynb)


<p align="right">(<a href="#readme-top">back to top</a>)</p>

