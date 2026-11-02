# X-QSL Amateur Radio ADIF Tool · Python + PyQt6 v0.9

基于原 X-QSL / CallSignAnalysis 项目的 Python + PyQt6 迁移版。
原项目链接：https://gitee.com/yuzhenwu/x-qsl-amateur-radio-adif-tool

## 日志流程


1. 顶部选择卫星。
2. 顶部使用“设定 / 实时”两个互锁单选框控制日志时间，默认“设定”。
3. “设定”模式可以手动选择 UTC 日志时间；“实时”模式下时间框每秒自动更新为当前 UTC 时间。
4. 输入呼号并使用呼号库模糊搜索。
5. 对支持多模式的卫星，使用顶部互锁单选框选择模式。FM 等单模式卫星不显示模式选择区域。
6. 在呼号输入框按回车直接加入日志。
7. 加入日志时会把当时的卫星、时间、模式和所选频率固定保存到该行，后续切换顶部配置不会影响已有记录。
8. 表格显示呼号、卫星名称、时间、频率和模式；卫星、频率及模式为只读文本。
9. 点击底部“导出ADIF”，生成并保存 ADIF 文件。

## satellites.json

卫星名称、别名、上下行频率和模式配置全部放在此文件中。一个卫星可以包含多个模式。可选字段 `adif_name` 用于指定 ADIF 中的 `SAT_NAME`；`frequency_options_mhz` 用于配置可选择的收发同频频率。

内置 APRS 记录项：

- `ARISS-APRS`：ADIF 卫星识别名为 `ARISS`，模式 `PKT`，频率可选 145.825、437.825、437.550 MHz。
- `SONATE-2-APRS`：ADIF 卫星识别名为 `SONATE`，模式 `PKT`，频率固定为 145.825 MHz。

这两项的 ADIF `FREQ` 与 `FREQ_RX` 相同，收发频段也按所选频率分别写入。

例如：

```json
{
  "name": "RS-44",
  "aliases": ["RS-44"],
  "uplink_mhz": 145.965,
  "downlink_mhz": 435.6,
  "modes": ["SSB", "CW"]
}
```

FM 单模式卫星配置为单项 `modes` 数组，例如 `['FM']`。程序不会显示模式选择区域。

## callsigns.txt

每行一个呼号。添加日志时，如果新呼号不存在于呼号库，程序会自动写入 `data/callsigns.txt`，并按照字母数字顺序重新排序。

## 运行

```bash
pip install -r requirements.txt
python main.py
```

## 编译

```bash
PyInstaller --clean --noconfirm --onefile --windowed --name XQSL_PyQt --icon=resources/app.ico --add-data "data;data" --add-data "resources;resources" main.py
```
