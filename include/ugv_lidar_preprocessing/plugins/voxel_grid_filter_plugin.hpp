#pragma once

#include <pcl/point_cloud.h>

#include "ugv_lidar_preprocessing/dtypes/plugin_params.hpp"
#include "ugv_lidar_preprocessing/plugins/plugin_interface.hpp"

namespace lidar_preprocessing_plugins
{
template<typename PointT>
class VoxelGridFilterPlugin : public ILidarPreProcessingPlugin<PointT>
{
public:
    using PointCloud = pcl::PointCloud<PointT>;

    VoxelGridFilterPlugin() = default;
    ~VoxelGridFilterPlugin() = default;

    void initialize(const PreprocessingPluginParams &params) override;

    void process(const PointCloud &input, PointCloud &output) const override;

private:
    bool m_enabled{false};
    float m_leaf_size{0.1f};
};
}  // namespace lidar_preprocessing_plugins