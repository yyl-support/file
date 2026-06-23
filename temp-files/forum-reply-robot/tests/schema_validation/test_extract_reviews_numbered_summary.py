from src.ForumBot.SchemaValidation import extract_reviews


def test_numbered_summary_point_keeps_following_table_until_section_break():
    content = """背景
根据标准接口要求新增RevisionId属性
整体方案
在资源协作接口bmc.kepler.Systems.PCIEDevice.PCIeFunction中新增RevisionId属性
评审点
在资源协作接口bmc.kepler.Systems.PCIeDevice.PCIeFunction中新增RevisionId属性
评审点1：新增资源协作接口属性RevisionId
资源path:/bmc/kepler/Systems/{SystemId}/PCIDevices/{Id}/PCIeFunctions/{PCIeFunctionId}
资源interface：bmc.kepler.Systems.PCIeDevice.PCIeFunction
新增属性：RevisionId
| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 访问权限 | 属性来源 | 持久化类型 | 易变属性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RevisionId | y | true | true | PCIe功能的RevisionId，默认值：空 | R：ReadOnly | NA | 无需持久化 | true |
是否准备好AI预审
是
评审结论
评审通过
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 1
    assert points[0]["title"] == "评审点1：新增资源协作接口属性RevisionId"
    assert "资源interface：bmc.kepler.Systems.PCIeDevice.PCIeFunction" in points[0]["content"]
    assert "| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 访问权限 |" in points[0]["content"]
    assert "| RevisionId | y | true | true | PCIe功能的RevisionId，默认值：空 | R：ReadOnly |" in points[0]["content"]
    assert "是否准备好AI预审" not in points[0]["content"]
    assert "评审结论" not in points[0]["content"]


def test_review_point_title_keeps_all_property_names_and_uses_detail_before_conclusion():
    content = """背景
实现RAS事件能力开放。
评审点
评审点1：资源协作接口属性CurrentPeriodCacheUncorrectableECCErrorCount、LifeTimeCacheUncorrectableECCErrorCount、CorrectableError、UncorrectableError
资源协作接口bmc.kepler.Systems.FDMDomain.NPURAS下新增属性
CurrentPeriodCacheUncorrectableECCErrorCount：NPU启动周期内Cache UCE统计计数
LifeTimeCacheUncorrectableECCErrorCount：NPU生命周期内Cache UCE统计计数
CorrectableError：NPU CE故障原子能力
UncorrectableError：NPU UCE故障原子能力
详细描述
资源path：/bmc/kepler/Systems/:SystemId/FDMDomain/NPURAS/:Id
资源interface：bmc.kepler.Systems.FDMDomain.NPURAS
新增属性：
| 属性名称 | 签名 | 只读 | 变化通知 | 属性描述 | 取值范围 | 访问权限 | 属性来源 | 持久化类型 | 易变属性 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CorrectableError | y | true | true | NPU发生可纠正错误，默认为0。系统上下电/系统复位/NPU复位，恢复为0。 | 0:未发生 1:发生 默认为0 | R：ReadOnly | 错误上报 | 复位持久化 | false |
是否准备好AI预审
是
评审结论
通过，具体结论
1.同意资源协作接口bmc.kepler.Systems.FDMDomain.NPURAS下新增属性
遗留问题
无
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 1
    assert points[0]["title"] == (
        "评审点1：资源协作接口属性CurrentPeriodCacheUncorrectableECCErrorCount、"
        "LifeTimeCacheUncorrectableECCErrorCount、CorrectableError、UncorrectableError"
    )
    assert "资源path：/bmc/kepler/Systems/:SystemId/FDMDomain/NPURAS/:Id" in points[0]["content"]
    assert "| CorrectableError | y | true | true |" in points[0]["content"]
    assert "1.同意资源协作接口" not in points[0]["content"]
    assert "遗留问题" not in points[0]["content"]


def test_unnumbered_summary_does_not_hide_numbered_detail_points():
    content = """背景
依据Redfish标准，Processor资源应当包含ProcessorMemory属性数组。
整体方案
在Processor资源查询接口响应体中新增ProcessorMemory数组属性，数据来源于新增的MDB资源协作接口。
评审点
Processor资源新增ProcessorMemory属性，以及新增MDB资源协作接口bmc.kepler.Systems.Processor.ProcessorMemory
详细描述
评审点1：Processor资源新增ProcessorMemory属性
资源URI：/redfish/v1/Systems/{SystemId}/Processors/{ProcessorId}
| 属性名 | 类型 | 描述 |
| --- | --- | --- |
| ProcessorMemory | array | 处理器内部的内存信息数组 |
CPU处理器或无内存信息的处理器：不返回ProcessorMemory属性。
评审点2：新增资源协作接口 bmc.kepler.Systems.Processor.ProcessorMemory
接口描述：提供处理器内存信息查询能力。
| 属性名称 | 签名 | 属性描述 |
| --- | --- | --- |
| CapacityMiB | t | 内存容量 |
评审点3：新增资源协作路径 /bmc/kepler/Systems/{SystemId}/Processors/{ProcessorType}/{ProcessorId}/ProcessorMemory/{MemoryType}
路径描述：用于存储和管理处理器内存配置信息。
| 实现接口 | 实现接口描述 |
| --- | --- |
| bmc.kepler.Systems.Processor.ProcessorMemory | 提供处理器内存信息查询功能 |
是否准备好AI预审
是
评审结论
同意
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 3
    assert points[0]["title"] == "评审点1：Processor资源新增ProcessorMemory属性"
    assert points[1]["title"] == "评审点2：新增资源协作接口 bmc.kepler.Systems.Processor.ProcessorMemory"
    assert points[2]["title"].startswith("评审点3：新增资源协作路径")
    assert "CPU处理器或无内存信息的处理器" in points[0]["content"]
    assert "接口描述：提供处理器内存信息查询能力。" in points[1]["content"]
    assert "是否准备好AI预审" not in points[2]["content"]


def test_english_review_points_from_detailed_description():
    content = """## Background
According to the Redfish standard, Processor should include ProcessorMemory.

## Overall Solution
Add ProcessorMemory to the Redfish response body, with data sourced from MDB.

## Review Points
Add the ProcessorMemory property to the Processor resource, as well as MDB resource collaboration interfaces.

## Detailed Description
### Review Point 1: Add ProcessorMemory Property to Processor Resource
**Resource URI**: `/redfish/v1/Systems/{SystemId}/Processors/{ProcessorId}`

| Property Name | Type | Description |
| --- | --- | --- |
| ProcessorMemory | array | Processor memory information |

### Review Point 2: Add Resource Collaboration Interface bmc.kepler.Systems.Processor.ProcessorMemory
**Interface Description**: Provides processor memory information.

| 属性名称 | 签名 | 属性描述 |
| --- | --- | --- |
| CapacityMiB | u | 内存容量 |

### Review Point 3: Add Resource Collaboration Path /bmc/kepler/Systems/{SystemId}/Processors/{ProcessorType}/{ProcessorId}/ProcessorMemory/{MemoryType}
Path description for processor memory resources.

| 实现接口 | 实现接口描述 |
| --- | --- |
| bmc.kepler.Systems.Processor.ProcessorMemory | Provides processor memory information |
"""

    points = extract_reviews.extract_all_review_points(content)

    assert len(points) == 3
    assert points[0]["title"] == "Review Point 1: Add ProcessorMemory Property to Processor Resource"
    assert points[1]["title"] == "Review Point 2: Add Resource Collaboration Interface bmc.kepler.Systems.Processor.ProcessorMemory"
    assert points[2]["title"].startswith("Review Point 3: Add Resource Collaboration Path")
    assert "/redfish/v1/Systems/{SystemId}/Processors/{ProcessorId}" in points[0]["content"]
    assert "CapacityMiB" in points[1]["content"]
    assert "实现接口" in points[2]["content"]
