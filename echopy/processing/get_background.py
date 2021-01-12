#!/usr/bin/env python3
"""
Algorithms for estimating background noise.
    
Copyright (c) 2020 Echopy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__authors__ = ['Alejandro Ariza'   # wrote derobertis()
               ]                                 
__credits__ = ['Rob Blackwell'     # supervised the code and provided ideas
               'Sophie Fielding'   # supervised the code and provided ideas               
               ]

import warnings
import numpy as np
from echopy import resample as rs

def derobertis(Sv, iax, jax, m, n, r, alpha, bgnmax=-125):
    """
    Estimate background noise as in:
        
        De Robertis and Higginbottom (2007) ‘A post-processing technique to 
        estimate the signal-to-noise ratio and remove echosounder background 
        noise’, ICES Journal of Marine Science, 64: 1282–1291.
    
    Args:
        Sv     (float)    : 2D array with Sv data (dB)
        iax    (int/float): 1D array with i axis (nsamples or metres)
        jax    (int/float): 1D array with j axis (npings, seconds, metres, etc)
        m      (int/float): i resampling length (nsamples or metres)
        n      (int/float): j resampling length (npings, seconds, metres, etc)
        r      (float)    : 1D array with range data (metres)
        alpha  (float)    : absorption coefficient value (dB m-1)
        bgnmax (int/float): maximum background noise estimation (dB)
    
    Returns:
        float: 2D numpy array with background noise estimation (dB)
        bool : 2D array with mask indicating valid noise estimation.
    """
    
    # calculate TVG 
    r_       = r.copy()
    r_[r<=0] = np.nan
    TVG      = 20*np.log10(r_) + 2*alpha*r_
    
    # subtract TVG from Sv  
    Sv_noTVG = Sv - np.vstack(TVG)
    
    # get resampled i/j axes    
    iaxrs       = np.arange(iax[0], iax[-1], m)
    jaxrs       = np.arange(jax[0], jax[-1], n)
    
    # proceed if length of resampled axes is greater than 1 
    if (len(iaxrs)>1) & (len(jaxrs)>1):
    
        # resample Sv_noTVG into m by n bins
        Sv_noTVGrs  = rs.twod(Sv_noTVG, iax, jax, iaxrs, jaxrs, log=True)[0]
        
        # compute background noise as the minimun value per interval in Sv_noTVGrs
        jbool                = np.isnan(Sv_noTVGrs).all(axis=0)
        Sv_noTVGrs [:,jbool] = 0
        bgn_noTVGrs          = np.nanmin(Sv_noTVGrs, 0)
        bgn_noTVGrs[  jbool] = np.nan
        bgn_noTVGrs          = np.tile(bgn_noTVGrs, [len(Sv_noTVGrs), 1])
            
        # Prevent to exceed the maximum background noise expected
        mask              = np.ma.masked_greater(bgn_noTVGrs, bgnmax).mask
        bgn_noTVGrs[mask] = bgnmax
        
        # resample background noise to previous Sv resolution, and add TVG
        bgn_noTVG, mask_ = rs.full(bgn_noTVGrs, iaxrs, jaxrs, iax, jax)
        bgn              = bgn_noTVG + np.vstack(TVG)
    
    # return background noise as NAN values otherwise    
    else:
        bgn   = np.ones_like(Sv)*np.nan
        mask_ = np.ones_like(Sv, dtype=bool)
        warnings.warn("unable to estimate background noise, incorrect resampling axes", RuntimeWarning)
    
    return bgn, mask_

def other():
    """
    Note to contributors:
        Other algorithms for estimating background noise must be named with the
        author or method name. If already published, the full citation must be
        provided. Please, add "unpub." otherwise. E.g: Smith et al. (unpub.)
        
        Please, check contribute.md to follow our coding and documenting style.
    """