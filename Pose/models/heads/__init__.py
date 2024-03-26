# Copyright (c) OpenMMLab. All rights reserved.
from .base_head import BaseHead
from .coord_cls_heads import RTMCCHead
# from .heatmap_heads import (AssociativeEmbeddingHead, CIDHead, CPMHead,
#                             HeatmapHead, InternetHead, MSPNHead, ViPNASHead)
# from .hybrid_heads import DEKRHead, RTMOHead, VisPredictHead
# from .regression_heads import (DSNTHead, IntegralRegressionHead,
#                                MotionRegressionHead, RegressionHead, RLEHead,
#                                TemporalRegressionHead,
#                                TrajectoryRegressionHead)
# from .transformer_heads import EDPoseHead

__all__ = [
    'BaseHead', 'RTMCCHead'
]
