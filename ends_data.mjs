// The makers' published figures for the ends on this page (mass, size, load, power and interfaces), each with its
// sources: maker pages, manuals, papers, resellers. Generated; do not edit here.
export const GRIPPERS=[
 {"id":"dex1","maker":"宇树 Unitree","model":"Dex1-1","stroke":90,"force":[5,120],"mass":0.55,"length":143,"width":78,"supply":"24–64 V（推荐 24 / 48 V，峰值 3.5 A）","bus":"高速 RS-485（6 Mbps，1 kHz）","src":["dex1Page","dex1Urdf","dex1Service","dex1Store","dex1StoreV2"]},
 {"id":"z1g","maker":"宇树 Unitree","model":"Z1 夹爪","stroke":null,"opening":"张角 90°","force":null,"forceText":"峰值 200（张口端 150）","mass":0.75,"length":139,"width":80,"supply":"24 V（峰值 70 W）","bus":"RS-485","src":["z1Gripper","z1Urdf"]}
];
export const UNITREE_OTHERS=[
 {"model":"Dex2/5","kind":"五指手（齿轮加腱绳驱动）","dof":"10 个关节、2 个电机（拇指一个，四指共用一个）","mass":0.365,"size":"151 × 70 × 63 mm","load":"1.5 kg（握 5 cm 圆形硬物）","power":"24–60 V，RS-485","src":"dex25Page"},
 {"model":"Dex3-1","kind":"三指灵巧手","dof":"7（拇指 3、食指 2、中指 2），33 个压力传感器","mass":0.71,"size":"175 × 88 × 77 mm","load":"0.5 kg","power":"12–58 V，USB 2.0","src":"dex31Page"},
 {"model":"Dex5-1 / Dex5-1P","kind":"五指灵巧手","dof":"20（16 个主动）；P 版 94 个压力传感器","mass":1.1,"size":"217 × 128 × 72 mm","load":"3.5 kg（掌心向下）","power":"24–60 V，USB 2.0","src":"dex51Page"},
 {"model":"Dex5-S / Dex5-S Pro","kind":"五指灵巧手","dof":"22，全部直驱、可反驱；Pro 带触觉","mass":0.62,"size":"102 × 187 × 26 mm","load":"持续 1 kg，峰值 2 kg","power":"15–65 V，千兆以太网、USB 或 RS-485","src":"dex5sPage"},
 {"model":"D1-T 机械臂","kind":"6 轴舵机臂，带夹爪","dof":"6 + 夹爪","mass":2.37,"size":"工作半径 550 mm（含夹爪 670 mm）","load":"0.5 kg","power":"24 V","src":"d1tPage","note":"夹爪是臂的一部分，官网没有单卖"}
];
export const SOURCES={
 "dex1Page":{"title":"宇树 Dex1-1 产品页（参数表）","url":"https://www.unitree.com/cn/Dex1-1","kind":"maker"},
 "dex1Urdf":{"title":"宇树 unitree_ros：Dex1-1 的 URDF 和网格（BSD-3-Clause，提交 8927c58）","url":"https://github.com/unitreerobotics/unitree_ros/tree/8927c58e133b5e234e78b8581016f9a4867e9e1c/robots/dexterous_hand_description/dex1_1","kind":"maker"},
 "dex1Service":{"title":"宇树 dex1_1_service：Dex1-1 的串口转 DDS 服务（BSD-3-Clause）","url":"https://github.com/unitreerobotics/dex1_1_service","kind":"maker"},
 "dex1Store":{"title":"Robostore：Dex1-1 V1 标准版（单只 380 美元，含 D405 支架、485 转 USB 板）","url":"https://robostore.com/products/unitree-dex1-1-v1-standard-gripper","kind":"reseller"},
 "dex1StoreV2":{"title":"Robostore：Dex1-1 V2 进阶版（单只 580 美元，加 160° RGB 相机）","url":"https://robostore.com/products/unitree-dex1-1-v2-advanced-gripper-rgb-camera","kind":"reseller"},
 "z1Gripper":{"title":"Weston Robot 文档：Unitree Z1 夹爪参数（经销商）","url":"https://westonrobot.github.io/docs-legacy/robot_user_guide/unitree/z1.html","kind":"reseller"},
 "z1Urdf":{"title":"宇树 unitree_ros：Z1 的 xacro（夹爪定爪 0.526 kg、动爪 0.276 kg，转动关节）","url":"https://github.com/unitreerobotics/unitree_ros/blob/master/robots/z1_description/xacro/robot.xacro","kind":"maker"},
 "dex25Page":{"title":"Unitree Dex2/5 产品页","url":"https://www.unitree.com/Dex2-5","kind":"maker"},
 "dex31Page":{"title":"Unitree Dex3-1 产品页","url":"https://www.unitree.com/Dex3-1","kind":"maker"},
 "dex51Page":{"title":"Unitree Dex5-1 产品页","url":"https://www.unitree.com/Dex5-1","kind":"maker"},
 "dex5sPage":{"title":"Unitree Dex5-S 产品页","url":"https://www.unitree.com/Dex5-S","kind":"maker"},
 "d1tPage":{"title":"Unitree D1-T 产品页","url":"https://www.unitree.com/D1-T","kind":"maker"}
};
export const OTHER_HANDS=[
 {"id":"inspire_rh56dfx","group":"cn","maker":"因时","makerEn":"Inspire Robots","model":"RH56DFX","kind":"五指灵巧手（微型电缸推连杆）","dof":"6 个主动自由度，12 个关节","mass":0.54,"size":null,"load":"拇指最大抓握力 15 N，四指 10 N","power":"DC 24 V ±10%（最大 2 A）；RS-485","src":["inspirePage","inspireModel"],"note":"模型取自宇树 xr_teleoperate（宇树人形机器人配的因时手）；因时官网只给 STEP（RAR 压缩包），没有 URDF"},
 {"id":"linker_l20","group":"cn","maker":"灵心巧手","makerEn":"LinkerBot","model":"Linker Hand L20","kind":"五指灵巧手（无刷电机、滚珠丝杠推连杆）","dof":"16 个主动、5 个被动，共 21 个关节","mass":1.2,"massText":"约 1.2 kg","size":null,"load":"最大负载 20 kg；五指抓握力 100 N，指尖力拇指 15 N、四指 20 N","power":"DC 24–48 V；CAN / RS-485","src":["linkerL20Page","linkerL20Manual"],"note":"URDF 各连杆质量合计只有 0.2 kg，和官网的约 1.2 kg 差得多，以官网为准"},
 {"id":"linker_o6","group":"cn","maker":"灵心巧手","makerEn":"LinkerBot","model":"Linker Hand O6","kind":"五指灵巧手（蜗轮蜗杆）","dof":"6 个主动、5 个被动自由度","mass":0.36,"size":null,"load":"最大负载 50 kg；五指抓握力 70 N，指尖力拇指 20 N、四指 25 N","power":"官网参数图里，文字没写","src":["linkerO6Page"],"note":"官网照片有蓝色款，这里按 URDF 的灰黑配色"},
 {"id":"brainco_revo2","group":"cn","maker":"强脑科技","makerEn":"BrainCo","model":"Revo2","kind":"五指灵巧手","dof":"6 个主动自由度，11 个关节（URDF：5 个关节随动）","mass":0.383,"size":"长 16 cm","load":"抓握力 50 N，可提 20 kg","power":"新闻稿没写","src":["braincoRelease"],"note":"厂家说比同类轻约 20%"},
 {"id":"oymotion_rohand","group":"cn","maker":"傲意科技","makerEn":"OYMotion","model":"ROHand","kind":"五指灵巧手（丝杆滑块推连杆）","dof":"6 个主动自由度，11 个关节","mass":0.486,"massText":"ROH-LiteS001 为 486 g（含手腕）","size":"ROH-LiteS001：中指尖到手腕 169 mm，掌宽 76 mm","load":"手册的这一型没写负载","power":"UART / RS-485 / CAN","src":["oymotionManual"],"note":"傲意的 URDF 没写是哪一型（ROH-A001、A002、AP001、LiteS001 外形相近）；手指是连杆，按傲意自己的连杆公式算各关节"},
 {"id":"dexrobot_dexhand021","group":"cn","maker":"灵巧智能","makerEn":"DexRobot","model":"DexHand021","kind":"五指灵巧手（腱绳驱动）","dof":"12 个主动、7 个被动，共 19 个自由度","mass":1,"massText":"约 1 kg","size":null,"load":"单指负载超过 10 N","power":"论文没写","src":["dexPaper"],"note":"参数取自厂家团队的论文，官网是脚本渲染的页面，读不到参数表"},
 {"id":"wuji_hand","group":"cn","maker":"舞肌科技","makerEn":"Wuji","model":"Wuji Hand 2.1","kind":"五指灵巧手（每个关节直驱）","dof":"20 个主动自由度（每指 4 个）","mass":0.8,"massText":"800 g（含软垫和线缆，不含转接件）","size":"180 × 80 × 40 mm","load":"文档没写","power":"DC 12 V；以太网","src":["wujiDocs"],"note":"2.1 是 Beta 样机，厂家说参数不代表最终产品；第一代 Wuji Hand 已停售"},
 {"id":"robotera_xhand1","group":"cn","maker":"星动纪元","makerEn":"RobotEra","model":"XHAND1 Pro-U","kind":"五指灵巧手（XHAND1 Pro 为 DexUMI 数据采集改型）","dof":"16 个主动，共 20 个关节（4 个耦合）","mass":null,"size":null,"load":"没写","power":"EtherCAT / RS-485（规格草案）","src":["xhandReadme"],"note":"星动纪元只公开了 Pro-U 的模型；标准版 XHAND1 是 12 个全主动自由度，没有公开模型"},
 {"id":"sharpa_wave","group":"intl","maker":"Sharpa","makerEn":"Sharpa（新加坡）","model":"SharpaWave（W01）","kind":"五指灵巧手（22 个自研驱动模组）","dof":"22 个主动自由度","mass":1.3,"size":"208 × 90 × 50 mm","load":"负载 40 kg，抓握力 150 N，指尖力 20 N（同表另一列为 24 kg、90 N、12 N，页面没写两列的区别）","power":"18–28 V；千兆以太网","src":["sharpaPage"],"note":"指尖有触觉阵列；绿色是 URDF 里标出的弹性体"},
 {"id":"shadow_hand","group":"intl","maker":"Shadow Robot","makerEn":"Shadow Robot（英国）","model":"Shadow Dexterous Hand（E 系列）","kind":"五指灵巧手（20 个电机装在前臂里，腱绳驱动）","dof":"20 个主动自由度、24 个关节，另有手腕 2 个","mass":4.3,"massText":"手和前臂共 4.3 kg","size":"和成年男性的手相近","load":"握持最多 4 kg","power":"EtherCAT（100 Mbps）","src":["shadowSpec"],"note":"模型是 MuJoCo Menagerie 的 E3M5（Shadow 提供，Apache-2.0），含前臂"},
 {"id":"allegro_v5","group":"intl","maker":"Wonik Robotics","makerEn":"Wonik Robotics（韩国）","model":"Allegro Hand V5（四指）","kind":"四指灵巧手（每个关节一个电机）","dof":"16 个主动自由度（四指各 4 个）","mass":null,"size":null,"load":"没查到厂家数据","power":"CAN","src":["allegroRepo"],"note":"官网参数页没能取到；模型是官方 ROS 2 软件里的 B 型"},
 {"id":"leap_hand","group":"intl","maker":"卡内基梅隆大学","makerEn":"CMU（美国）","model":"LEAP Hand","kind":"四指灵巧手（16 个 Dynamixel 舵机）","dof":"16 个主动自由度","mass":null,"size":null,"load":"论文没给负载","power":"Dynamixel 总线（U2D2 转 USB）","src":["leapPaper"],"note":"开源，零件约 2000 美元，4 小时装好；仿真仓库为 MIT，LEAP 的 CAD 另标 CC BY-NC-SA（非商用）"},
 {"id":"ability_hand","group":"intl","maker":"PSYONIC","makerEn":"PSYONIC（美国）","model":"Ability Hand","kind":"五指仿生手（义肢，也做机器人版）","dof":"6 个主动自由度，10 个关节（URDF：4 个随动）","mass":0.49,"size":null,"load":"官网没写","power":"官网没写","src":["psyonicPage"],"note":"32 种抓握模式；URDF 是大号手"},
 {"id":"tesollo_dg5f","group":"intl","maker":"Tesollo","makerEn":"Tesollo（韩国）","model":"DG-5F（DG-5F-M）","kind":"五指灵巧手（每指 4 个电机）","dof":"20 个主动自由度（每指 4 个）","mass":1.763,"size":null,"load":"捏取 2.5 kg（最大 5 kg），包络 10 kg（最大 20 kg）","power":"24 V；Modbus RTU/TCP、以太网","src":["tesolloPage"],"note":"颜色取自 Tesollo 网格自带的材质"}
];
export const HAND_SOURCES={
 "inspirePage":{"title":"因时 RH56DFX 系列产品页（参数表）","url":"https://www.inspire-robots.com/dexterous%20hands/rh56dfx-series/","kind":"maker"},
 "inspireModel":{"title":"宇树 xr_teleoperate：因时手的 URDF 和网格（Apache-2.0）","url":"https://github.com/unitreerobotics/xr_teleoperate/tree/main/assets/inspire_hand","kind":"maker"},
 "linkerL20Page":{"title":"灵心巧手 Linker Hand L20 产品页","url":"https://www.linkerbot.cn/details/LinkerHandL20","kind":"maker"},
 "linkerL20Manual":{"title":"Linker Hand L20 产品手册 V1.0（2026-03-24）","url":"https://a.storyblok.com/f/298593/x/50a0fc9e84/linker-hand-l20-v10-20260324.pdf","kind":"maker"},
 "linkerO6Page":{"title":"灵心巧手 Linker Hand O6 产品页","url":"https://www.linkerbot.cn/details/LinkerHandO6","kind":"maker"},
 "braincoRelease":{"title":"BrainCo 发布 Revo2 的新闻稿（Robotics Tomorrow 转载）","url":"https://www.roboticstomorrow.com/content.php?post=25536","kind":"maker"},
 "oymotionManual":{"title":"傲意 ROH-LiteS001 灵巧手手册 V1.0.7","url":"https://oymotion.github.io/en/ROHand/imgs/ROH-LiteS001-Dexterous-Hand-V1.0.7.pdf","kind":"maker"},
 "dexPaper":{"title":"DexHand 021 论文（arXiv 2511.03481，灵巧智能团队）","url":"https://arxiv.org/abs/2511.03481","kind":"paper"},
 "wujiDocs":{"title":"舞肌 Wuji Hand 2.1 文档：产品介绍（Beta）","url":"https://docs.wuji.tech/docs/en/wuji-hand/beta1/overview","kind":"maker"},
 "xhandReadme":{"title":"星动纪元 xhand1-pro-u 仓库说明（XHAND1 Pro-U 参数）","url":"https://github.com/roboterax/xhand1-pro-u","kind":"maker"},
 "sharpaPage":{"title":"Sharpa Wave（W01）产品页","url":"https://www.sharpa.com/pages/w01","kind":"maker"},
 "shadowSpec":{"title":"Shadow Dexterous Hand 技术规格（2025）","url":"https://shadowrobot.com/wp-content/uploads/2025/09/shadow_dexterous_hand_e_technical_specification.pdf","kind":"maker"},
 "allegroRepo":{"title":"Wonik Robotics allegro_hand_ros2_v5（官方 ROS 2 软件和 URDF）","url":"https://github.com/Wonikrobotics-git/allegro_hand_ros2_v5","kind":"maker"},
 "leapPaper":{"title":"LEAP Hand 论文（arXiv 2309.06440，CMU）","url":"https://arxiv.org/abs/2309.06440","kind":"paper"},
 "psyonicPage":{"title":"PSYONIC Ability Hand 产品页","url":"https://www.psyonic.io/ability-hand","kind":"maker"},
 "tesolloPage":{"title":"Tesollo DG-5F-M 产品页","url":"https://en.tesollo.com/dg-5f-m","kind":"maker"}
};
