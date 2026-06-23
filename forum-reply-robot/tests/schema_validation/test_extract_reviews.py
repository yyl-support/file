from src.ForumBot.SchemaValidation import extract_reviews


def test_is_redfish_related_detects_keyword():
    assert extract_reviews.is_redfish_related("Need help", "Using Redfish API") is True
    assert extract_reviews.is_redfish_related("Need help", "No platform keyword") is False


def test_extracts_single_unnumbered_review_point_with_detail_section():
    content = """背景
某客户需要北向redfish接口获取硬盘控制器和颗粒厂商、型号信息。
评审点
资源协作接口 bmc.kepler.Systems.Storage.StorageConfig 下新增属性 DriveControllerInfoEnabled 控制BMC是否采集硬盘控制器和NAND颗粒信息，默认关闭。
详细描述
变更描述：在已有对象StorageConfig下新增属性
属性名称
签名
只读
变化通知
属性描述
访问权限
属性来源
持久化类型
变更影响
DriveControllerInfoEnabled
b
false
false
硬盘控制器、颗粒信息获取使能开关
R：ReadOnly W：BasicSetting
产品配置
不持久化
无影响
是否准备好AI预审
是
评审结论
同意新增属性
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 1
    assert points[0]["title"].startswith("评审点1：资源协作接口")
    assert "DriveControllerInfoEnabled" in points[0]["content"]
    assert "访问权限" in points[0]["content"]
    assert "是否准备好AI预审" not in points[0]["content"]


def test_single_unnumbered_review_point_allows_numbered_detail_list():
    content = """背景
客户需要北向redfish接口获取硬盘控制器信息。
评审点
资源协作接口 bmc.kepler.Systems.Storage.StorageConfig 下新增属性 DriveControllerInfoEnabled。
详细描述
变更描述：
1. 在已有对象StorageConfig下新增属性
2. 默认关闭，不影响已有流程
是否准备好AI预审
是
评审结论
同意
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 1
    assert points[0]["title"].startswith("评审点1：资源协作接口")
    assert "1. 在已有对象StorageConfig下新增属性" in points[0]["content"]
    assert "2. 默认关闭" in points[0]["content"]
