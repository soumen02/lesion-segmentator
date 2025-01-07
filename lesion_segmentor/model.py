from monai.networks.nets import SegResNet

def get_network():
    return SegResNet(
        spatial_dims=3,
        in_channels=1,
        out_channels=2,  # background + lesion
        init_filters=32,
        blocks_down=(1, 2, 2, 4),
        blocks_up=(1, 1, 1),
        dropout_prob=0.2,
    ) 