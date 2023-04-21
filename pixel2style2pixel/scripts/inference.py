import os
from argparse import Namespace

from tqdm import tqdm
import time
import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader
import sys

import pandas as pd

sys.path.append(".")
sys.path.append("..")

from configs import data_configs
from datasets.inference_dataset import InferenceDataset
from utils.common import tensor2im, log_input_image
from options.test_options import TestOptions
from models.psp import pSp


def run():
    test_opts = TestOptions().parse()

    if test_opts.resize_factors is not None:
        assert len(
            test_opts.resize_factors.split(',')) == 1, "When running inference, provide a single downsampling factor!"
        out_path_results = os.path.join(test_opts.exp_dir, 'inference_results',
                                        'downsampling_{}'.format(test_opts.resize_factors))
        out_path_coupled = os.path.join(test_opts.exp_dir, 'inference_coupled',
                                        'downsampling_{}'.format(test_opts.resize_factors))
    else:
        out_path_results = os.path.join(test_opts.exp_dir, 'inference_results')
        out_path_coupled = os.path.join(test_opts.exp_dir, 'inference_coupled')

    os.makedirs(out_path_results, exist_ok=True)
    os.makedirs(out_path_coupled, exist_ok=True)

    # update test options with options used during training
    ckpt = torch.load(test_opts.checkpoint_path, map_location='cpu')
    opts = ckpt['opts']
    opts.update(vars(test_opts))
    if 'learn_in_w' not in opts:
        opts['learn_in_w'] = False
    if 'output_size' not in opts:
        opts['output_size'] = 1024
    opts = Namespace(**opts)

    net = pSp(opts)
    net.eval()
    net.cuda()

    print('Loading dataset for {}'.format(opts.dataset_type))
    dataset_args = data_configs.DATASETS[opts.dataset_type]
    transforms_dict = dataset_args['transforms'](opts).get_transforms()
    dataset = InferenceDataset(root=opts.data_path,
                               transform=transforms_dict['transform_inference'],
                               opts=opts)
    dataloader = DataLoader(dataset,
                            batch_size=opts.test_batch_size,
                            shuffle=False,
                            num_workers=int(opts.test_workers),
                            drop_last=True)

    if opts.n_images is None:
        opts.n_images = len(dataset)

    global_i = 0
    global_time = []
    image_name = []

    if test_opts.save_latent_type == "W":
      W_code = np.zeros((opts.n_images,512),dtype='float32')
      tmp_W_path = opts.exp_dir + '/W_512'
    elif test_opts.save_latent_type == "Wplus_all":
      W_code = np.zeros((opts.n_images, 18, 512),dtype='float32')
      tmp_W_path = opts.exp_dir + '/Wplus_all_layers'
    elif test_opts.save_latent_type == "Wplus_one_layer":
      W_code = np.zeros((opts.n_images,512),dtype='float32')
      tmp_W_path = opts.exp_dir + '/Wplus_layer_' + str(test_opts.save_latent_layer)   
    else:
      raise ValueError("Invalid save_latent_type option")

    
    for input_batch in tqdm(dataloader):
        if global_i >= opts.n_images:
            break
        with torch.no_grad():
            input_cuda = input_batch.cuda().float()
            tic = time.time()
            #result_batch = run_on_batch(input_cuda, net, opts)
            result_batch, result_batch_latent = run_on_batch(input_cuda, net, opts)
            toc = time.time()
            global_time.append(toc - tic)

        for i in range(opts.test_batch_size):
            result = tensor2im(result_batch[i])
            im_path = dataset.paths[global_i]
            if test_opts.save_latent_type == "W":
              print("Extract just W vector")
              result_latent_code = result_batch_latent[i][0]
            elif test_opts.save_latent_type == "Wplus_all":
              print("Extract just W+ all layers")
              result_latent_code = result_batch_latent[i]
            elif test_opts.save_latent_type == "Wplus_one_layer":
              print("Extract W+ layer: ", test_opts.save_latent_layer)
              result_latent_code = result_batch_latent[i][test_opts.save_latent_layer]
            else: 
              raise ValueError("Invalid save_latent_type")

            if opts.couple_outputs or global_i % 100 == 0:
                input_im = log_input_image(input_batch[i], opts)
                resize_amount = (256, 256) if opts.resize_outputs else (opts.output_size, opts.output_size)
                if opts.resize_factors is not None:
                    # for super resolution, save the original, down-sampled, and output
                    source = Image.open(im_path)
                    res = np.concatenate([np.array(source.resize(resize_amount)),
                                          np.array(input_im.resize(resize_amount, resample=Image.NEAREST)),
                                          np.array(result.resize(resize_amount))], axis=1)
                else:
                    # otherwise, save the original and output
                    res = np.concatenate([np.array(input_im.resize(resize_amount)),
                                          np.array(result.resize(resize_amount))], axis=1)
                Image.fromarray(res).save(os.path.join(out_path_coupled, os.path.basename(im_path)))

            im_save_path = os.path.join(out_path_results,  "encoded_"+os.path.basename(im_path))
            image_name.append(os.path.basename(im_path))
            W_code[global_i,:] = result_latent_code.to('cpu').detach().numpy().copy()
            Image.fromarray(np.array(result)).save(im_save_path)
            
            global_i += 1
            

    stats_path = os.path.join(opts.exp_dir, 'stats.txt')
    img_name_path =  os.path.join(opts.exp_dir, 'image_name.csv')
    result_str = 'Runtime {:.4f}+-{:.4f}'.format(np.mean(global_time), np.std(global_time))
    print(result_str)
    print(image_name)
    image_name_df = pd.DataFrame(image_name, columns =['image_name'])
    image_name_df.to_csv(img_name_path)
    np.save(tmp_W_path,W_code)

    with open(stats_path, 'w') as f:
        f.write(result_str)


def run_on_batch(inputs, net, opts):
    if opts.latent_mask is None:
        result_batch, result_batch_latent= net(inputs, randomize_noise=False, return_latents=True, resize=opts.resize_outputs)
    else:
        latent_mask = [int(l) for l in opts.latent_mask.split(",")]
        result_batch = []
        for image_idx, input_image in enumerate(inputs):
            # get latent vector to inject into our input image
            vec_to_inject = np.random.randn(1, 512).astype('float32')
            _, latent_to_inject = net(torch.from_numpy(vec_to_inject).to("cuda"),
                                      input_code=True,
                                      return_latents=True)
            # get output image with injected style vector
            res = net(input_image.unsqueeze(0).to("cuda").float(),
                      latent_mask=latent_mask,
                      inject_latent=latent_to_inject,
                      alpha=opts.mix_alpha,
                      resize=opts.resize_outputs)
            result_batch.append(res)
        result_batch = torch.cat(result_batch, dim=0)
    return result_batch, result_batch_latent


if __name__ == '__main__':
    run()
