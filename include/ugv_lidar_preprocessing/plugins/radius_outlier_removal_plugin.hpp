#pragma once

#include <pcl/point_cloud.h>

#include "ugv_lidar_preprocessing/dtypes/plugin_params.hpp"
#include "ugv_lidar_preprocessing/plugins/plugin_interface.hpp"

namespace lidar_preprocessing_plugins
{
template<typename PointT>
class RadiusOutlierRemovalPlugin : public ILidarPreProcessingPlugin<PointT>
{
public:
    using PointCloud = pcl::PointCloud<PointT>;

    RadiusOutlierRemovalPlugin() = default;
    ~RadiusOutlierRemovalPlugin() = default;

    void initialize(const PreprocessingPluginParams &params) override;

    void process(const PointCloud &input, PointCloud &output) const override;

private:
    bool m_enabled{false};
    double m_radius{0.5};
    int m_min_neighbors{5};
};
}  // namespace lidar_preprocessing_plugins