from app.database import SessionLocal, engine
from app.models.database_models import Base, Script

# 创建所有数据库表（如果不存在）
Base.metadata.create_all(bind=engine)

# 创建数据库会话
db = SessionLocal()

# 检查数据库中是否已有剧本数据，避免重复插入
if db.query(Script).first() is None:
    print("正在创建初始剧本数据...")

    # 原有的8个剧本数据
    scripts_data = [
        {
            "id": "1",
            "title": "午夜图书馆",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["悬疑", "本格", "微恐"],
            "players": "6人 (3男3女)",
            "difficulty": 4,
            "duration": "约4小时",
            "author": "神秘作者",
            "description": "深夜的图书馆中，一位管理员神秘失踪。六位访客被困在这座古老的建筑中，必须在天亮前找出真相。每个人都有不可告人的秘密，而真相往往比想象中更加黑暗...",
            "characters": [
                {"name": "图书管理员", "avatar": "/placeholder.svg?height=60&width=60", "description": "知识渊博但性格孤僻的管理员"},
                {"name": "文学教授", "avatar": "/placeholder.svg?height=60&width=60", "description": "优雅的中年教授，对古籍情有独钟"},
                {"name": "神秘访客", "avatar": "/placeholder.svg?height=60&width=60", "description": "身份不明的年轻人，似乎在寻找什么"},
            ]
        },
        {
            "id": "2",
            "title": "雾都疑案",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Hardcore",
            "tags": ["硬核", "推理", "维多利亚"],
            "players": "7人 (4男3女)",
            "difficulty": 5,
            "duration": "约5小时",
            "author": "推理大师",
            "description": "19世纪的伦敦，浓雾笼罩的街道上发生了一起离奇的谋杀案。作为苏格兰场的精英侦探们，你们必须在48小时内破解这个看似不可能的密室杀人案...",
            "characters": [
                {"name": "首席探长", "avatar": "/placeholder.svg?height=60&width=60", "description": "经验丰富的老探长，直觉敏锐"},
                {"name": "法医专家", "avatar": "/placeholder.svg?height=60&width=60", "description": "年轻的法医，擅长尸体检验"},
            ]
        },
        {
            "id": "3",
            "title": "校园七不思议",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Horror",
            "tags": ["恐怖", "校园", "灵异"],
            "players": "5人 (2男3女)",
            "difficulty": 3,
            "duration": "约3小时",
            "author": "恐怖小说家",
            "description": "深夜的学校里流传着七个恐怖传说。当五位学生因为各种原因被困在校园中过夜时，他们发现这些传说正在一个个变成现实...",
            "characters": [
                {"name": "学生会长", "avatar": "/placeholder.svg?height=60&width=60", "description": "责任感强的优等生"},
                {"name": "问题学生", "avatar": "/placeholder.svg?height=60&width=60", "description": "叛逆的不良少年，实际上很善良"},
            ]
        },
        {
            "id": "4",
            "title": "豪门恩怨",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Emotional",
            "tags": ["情感", "家族", "商战"],
            "players": "8人 (4男4女)",
            "difficulty": 3,
            "duration": "约4小时",
            "author": "情感编剧",
            "description": "富豪家族的继承人突然离世，巨额遗产的分配引发了家族内部的明争暗斗。每个人都有继承的理由，也都有杀人的动机...",
            "characters": [
                {"name": "大少爷", "avatar": "/placeholder.svg?height=60&width=60", "description": "表面风光的继承人，内心充满压力"},
                {"name": "管家", "avatar": "/placeholder.svg?height=60&width=60", "description": "服务家族多年的忠诚管家"},
            ]
        },
        {
            "id": "5",
            "title": "太空站危机",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["科幻", "太空", "生存"],
            "players": "6人 (3男3女)",
            "difficulty": 4,
            "duration": "约4小时",
            "author": "科幻作家",
            "description": "2087年，国际空间站上的科研人员发现了一个惊人的秘密。但随着通讯中断，他们意识到危险不仅来自外太空，更来自身边的同伴...",
            "characters": [
                {"name": "指挥官", "avatar": "/placeholder.svg?height=60&width=60", "description": "经验丰富的太空站指挥官"},
                {"name": "科学家", "avatar": "/placeholder.svg?height=60&width=60", "description": "专注研究的天体物理学家"},
            ]
        },
        {
            "id": "6",
            "title": "古堡之谜",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Joyful",
            "tags": ["欢乐", "古堡", "轻松"],
            "players": "6人 (3男3女)",
            "difficulty": 2,
            "duration": "约3小时",
            "author": "喜剧编剧",
            "description": "一群朋友受邀到古堡度假，却发现这里隐藏着一个有趣的宝藏谜题。在轻松愉快的氛围中，大家需要通过合作和推理来解开古堡的秘密...",
            "characters": [
                {"name": "古堡主人", "avatar": "/placeholder.svg?height=60&width=60", "description": "幽默风趣的古堡继承人"},
                {"name": "历史学家", "avatar": "/placeholder.svg?height=60&width=60", "description": "对古代历史充满热情的学者"},
            ]
        },
        {
            "id": "7",
            "title": "深海实验室",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Horror",
            "tags": ["恐怖", "深海", "实验"],
            "players": "7人 (4男3女)",
            "difficulty": 4,
            "duration": "约5小时",
            "author": "恐怖大师",
            "description": "深海研究站中，科学家们正在进行一项秘密实验。当实验失控时，他们发现自己被困在了海底，而更可怕的是，实验体似乎还活着...",
            "characters": [
                {"name": "首席科学家", "avatar": "/placeholder.svg?height=60&width=60", "description": "野心勃勃的研究者"},
                {"name": "安全主管", "avatar": "/placeholder.svg?height=60&width=60", "description": "负责实验室安全的退役军人"},
            ]
        },
        {
            "id": "8",
            "title": "时光咖啡馆",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Emotional",
            "tags": ["情感", "时光", "温馨"],
            "players": "5人 (2男3女)",
            "difficulty": 2,
            "duration": "约3小时",
            "author": "温情作家",
            "description": "一家神奇的咖啡馆，据说能让人回到过去的某个时刻。五位顾客各自带着遗憾来到这里，他们能否在这里找到内心的平静...",
            "characters": [
                {"name": "咖啡馆老板", "avatar": "/placeholder.svg?height=60&width=60", "description": "神秘而温和的老板娘"},
                {"name": "失恋青年", "avatar": "/placeholder.svg?height=60&width=60", "description": "刚刚失恋的大学生"},
            ]
        },
        # 新增的12个剧本
        {
            "id": "9",
            "title": "江户怪谈",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Horror",
            "tags": ["恐怖", "江户", "妖怪"],
            "players": "6人 (3男3女)",
            "difficulty": 4,
            "duration": "约4小时",
            "author": "怪谈作家",
            "description": "江户时代的深夜，几位旅人在古老的客栈中过夜。随着夜色渐深，他们发现这里并非普通的客栈，而是妖怪们聚集的场所...",
            "characters": [
                {"name": "客栈老板", "avatar": "/placeholder.svg?height=60&width=60", "description": "表面和善的客栈老板，隐藏着秘密"},
                {"name": "武士", "avatar": "/placeholder.svg?height=60&width=60", "description": "正义感强烈的浪人武士"},
                {"name": "阴阳师", "avatar": "/placeholder.svg?height=60&width=60", "description": "能够看见妖怪的神秘术士"},
                {"name": "商人", "avatar": "/placeholder.svg?height=60&width=60", "description": "精明的江户商人，贪财但不失良心"},
            ]
        },
        {
            "id": "10",
            "title": "赛博朋克2099",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["科幻", "赛博朋克", "未来"],
            "players": "7人 (4男3女)",
            "difficulty": 5,
            "duration": "约5小时",
            "author": "未来作家",
            "description": "2099年的新东京，一名顶级黑客神秘死亡。在这个充满霓虹灯和人工智能的世界里，真相被层层代码所掩盖...",
            "characters": [
                {"name": "网络侦探", "avatar": "/placeholder.svg?height=60&width=60", "description": "专门调查网络犯罪的未来警察"},
                {"name": "AI研究员", "avatar": "/placeholder.svg?height=60&width=60", "description": "研究人工智能的天才科学家"},
                {"name": "企业间谍", "avatar": "/placeholder.svg?height=60&width=60", "description": "为大公司窃取情报的专业间谍"},
                {"name": "改造人", "avatar": "/placeholder.svg?height=60&width=60", "description": "身体大部分被机械改造的前军人"},
                {"name": "黑客", "avatar": "/placeholder.svg?height=60&width=60", "description": "地下世界的顶级黑客"},
            ]
        },
        {
            "id": "11",
            "title": "民国往事",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Emotional",
            "tags": ["民国", "情感", "历史"],
            "players": "6人 (3男3女)",
            "difficulty": 3,
            "duration": "约4小时",
            "author": "历史作家",
            "description": "1930年代的上海，在这个充满变革的时代里，几个不同身份的人因为一个秘密而聚集在一起。爱情、友情、家国情怀在这里交织...",
            "characters": [
                {"name": "报社记者", "avatar": "/placeholder.svg?height=60&width=60", "description": "追求真相的进步青年记者"},
                {"name": "大家闺秀", "avatar": "/placeholder.svg?height=60&width=60", "description": "出身名门但思想开放的女学生"},
                {"name": "革命党人", "avatar": "/placeholder.svg?height=60&width=60", "description": "为理想奋斗的热血青年"},
                {"name": "商人", "avatar": "/placeholder.svg?height=60&width=60", "description": "在乱世中求生存的精明商人"},
            ]
        },
        {
            "id": "12",
            "title": "魔法学院谜案",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Joyful",
            "tags": ["魔法", "学院", "奇幻"],
            "players": "8人 (4男4女)",
            "difficulty": 3,
            "duration": "约4小时",
            "author": "奇幻作家",
            "description": "在一所神秘的魔法学院里，学生们发现了一个古老的魔法谜题。为了解开这个谜题，他们必须运用各自的魔法技能和智慧...",
            "characters": [
                {"name": "院长", "avatar": "/placeholder.svg?height=60&width=60", "description": "睿智而神秘的魔法学院院长"},
                {"name": "优等生", "avatar": "/placeholder.svg?height=60&width=60", "description": "成绩优异的魔法学徒"},
                {"name": "调皮学生", "avatar": "/placeholder.svg?height=60&width=60", "description": "爱恶作剧但心地善良的学生"},
                {"name": "图书管理员", "avatar": "/placeholder.svg?height=60&width=60", "description": "掌管魔法书籍的神秘管理员"},
                {"name": "新生", "avatar": "/placeholder.svg?height=60&width=60", "description": "刚入学的魔法新手"},
            ]
        },
        {
            "id": "13",
            "title": "末日求生",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Hardcore",
            "tags": ["末日", "生存", "合作"],
            "players": "6人 (3男3女)",
            "difficulty": 5,
            "duration": "约6小时",
            "author": "末日作家",
            "description": "世界末日后的废土世界，幸存者们必须在资源匮乏的环境中生存下去。信任与背叛、合作与竞争，人性在极限环境下被彻底考验...",
            "characters": [
                {"name": "前军人", "avatar": "/placeholder.svg?height=60&width=60", "description": "有丰富战斗经验的退役军人"},
                {"name": "医生", "avatar": "/placeholder.svg?height=60&width=60", "description": "在末日中拯救生命的医务工作者"},
                {"name": "工程师", "avatar": "/placeholder.svg?height=60&width=60", "description": "能够修理各种设备的技术专家"},
                {"name": "商人", "avatar": "/placeholder.svg?height=60&width=60", "description": "在废土中进行物资交易的商人"},
            ]
        },
        {
            "id": "14",
            "title": "古代宫廷秘史",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["古代", "宫廷", "权谋"],
            "players": "7人 (4男3女)",
            "difficulty": 4,
            "duration": "约5小时",
            "author": "历史悬疑作家",
            "description": "唐朝盛世的皇宫中，一位重要大臣离奇死亡。在这个充满权谋和阴谋的地方，每个人都可能是凶手，也都可能是下一个受害者...",
            "characters": [
                {"name": "皇帝", "avatar": "/placeholder.svg?height=60&width=60", "description": "英明但多疑的一代明君"},
                {"name": "皇后", "avatar": "/placeholder.svg?height=60&width=60", "description": "美丽聪慧的皇后，深谙宫廷之道"},
                {"name": "太监总管", "avatar": "/placeholder.svg?height=60&width=60", "description": "掌握宫中大权的太监头子"},
                {"name": "御史大夫", "avatar": "/placeholder.svg?height=60&width=60", "description": "正直但固执的朝廷重臣"},
                {"name": "宫女", "avatar": "/placeholder.svg?height=60&width=60", "description": "看似柔弱实则机智的宫中女子"},
            ]
        },
        {
            "id": "15",
            "title": "温泉旅馆杀人事件",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["温泉", "旅馆", "本格推理"],
            "players": "8人 (4男4女)",
            "difficulty": 4,
            "duration": "约4小时",
            "author": "本格推理作家",
            "description": "在偏远山区的温泉旅馆中，一场暴风雪将客人们困在了这里。当第一具尸体被发现时，所有人都意识到凶手就在他们中间...",
            "characters": [
                {"name": "旅馆老板", "avatar": "/placeholder.svg?height=60&width=60", "description": "经营旅馆多年的老板"},
                {"name": "推理小说家", "avatar": "/placeholder.svg?height=60&width=60", "description": "专写推理小说的知名作家"},
                {"name": "退休警察", "avatar": "/placeholder.svg?height=60&width=60", "description": "经验丰富的退休老警察"},
                {"name": "年轻夫妇", "avatar": "/placeholder.svg?height=60&width=60", "description": "来度蜜月的新婚夫妇"},
                {"name": "商务人士", "avatar": "/placeholder.svg?height=60&width=60", "description": "出差途中的公司职员"},
                {"name": "大学生", "avatar": "/placeholder.svg?height=60&width=60", "description": "独自旅行的文学系学生"},
            ]
        },
        {
            "id": "16",
            "title": "青春校园祭",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Joyful",
            "tags": ["青春", "校园", "友情"],
            "players": "6人 (3男3女)",
            "difficulty": 2,
            "duration": "约3小时",
            "author": "青春作家",
            "description": "高中最后的文化祭即将到来，同学们为了让这次活动成功而努力准备。在这个过程中，友情、爱情和梦想交织在一起...",
            "characters": [
                {"name": "班长", "avatar": "/placeholder.svg?height=60&width=60", "description": "认真负责的班级领导者"},
                {"name": "艺术生", "avatar": "/placeholder.svg?height=60&width=60", "description": "富有创意的美术特长生"},
                {"name": "体育委员", "avatar": "/placeholder.svg?height=60&width=60", "description": "活力四射的运动健将"},
                {"name": "文学少女", "avatar": "/placeholder.svg?height=60&width=60", "description": "喜欢读书写作的安静女孩"},
            ]
        },
        {
            "id": "17",
            "title": "西部荒野传说",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Hardcore",
            "tags": ["西部", "牛仔", "冒险"],
            "players": "7人 (5男2女)",
            "difficulty": 4,
            "duration": "约5小时",
            "author": "西部作家",
            "description": "19世纪美国西部的小镇上，一群不同背景的人因为一个传说中的宝藏而聚集在一起。在这片法外之地，只有最强者才能生存...",
            "characters": [
                {"name": "赏金猎人", "avatar": "/placeholder.svg?height=60&width=60", "description": "冷酷无情的职业杀手"},
                {"name": "酒吧老板娘", "avatar": "/placeholder.svg?height=60&width=60", "description": "美丽而精明的酒吧经营者"},
                {"name": "牧师", "avatar": "/placeholder.svg?height=60&width=60", "description": "在荒野中传播信仰的神职人员"},
                {"name": "印第安向导", "avatar": "/placeholder.svg?height=60&width=60", "description": "熟悉地形的原住民向导"},
                {"name": "银行家", "avatar": "/placeholder.svg?height=60&width=60", "description": "贪婪但精明的金融家"},
            ]
        },
        {
            "id": "18",
            "title": "都市传说调查团",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Horror",
            "tags": ["都市传说", "调查", "超自然"],
            "players": "5人 (2男3女)",
            "difficulty": 3,
            "duration": "约4小时",
            "author": "都市传说作家",
            "description": "一群对超自然现象感兴趣的年轻人组成了都市传说调查团。这次他们要调查的是一个关于废弃医院的恐怖传说...",
            "characters": [
                {"name": "团长", "avatar": "/placeholder.svg?height=60&width=60", "description": "对超自然现象痴迷的大学生"},
                {"name": "摄影师", "avatar": "/placeholder.svg?height=60&width=60", "description": "专门拍摄灵异照片的摄影爱好者"},
                {"name": "心理学生", "avatar": "/placeholder.svg?height=60&width=60", "description": "试图用科学解释超自然现象的理性主义者"},
                {"name": "灵媒", "avatar": "/placeholder.svg?height=60&width=60", "description": "声称能与灵魂沟通的神秘女孩"},
            ]
        },
        {
            "id": "19",
            "title": "星际殖民地",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Mystery",
            "tags": ["科幻", "太空", "殖民"],
            "players": "6人 (3男3女)",
            "difficulty": 4,
            "duration": "约4小时",
            "author": "科幻推理作家",
            "description": "2150年，人类在遥远星球建立的殖民地突然失去联系。当救援队到达时，他们发现了一个令人困惑的谜团...",
            "characters": [
                {"name": "殖民地指挥官", "avatar": "/placeholder.svg?height=60&width=60", "description": "负责殖民地运营的资深指挥官"},
                {"name": "生物学家", "avatar": "/placeholder.svg?height=60&width=60", "description": "研究外星生物的科学家"},
                {"name": "工程师", "avatar": "/placeholder.svg?height=60&width=60", "description": "维护殖民地设施的技术专家"},
                {"name": "通讯员", "avatar": "/placeholder.svg?height=60&width=60", "description": "负责与地球联系的通讯专家"},
            ]
        },
        {
            "id": "20",
            "title": "音乐盒的秘密",
            "cover": "/placeholder.svg?height=300&width=200",
            "category": "Emotional",
            "tags": ["音乐", "回忆", "治愈"],
            "players": "4人 (2男2女)",
            "difficulty": 2,
            "duration": "约2小时",
            "author": "治愈系作家",
            "description": "一个古老的音乐盒承载着几代人的回忆和秘密。当四个不同年龄的人因为这个音乐盒而相遇时，他们发现了关于爱与失去的真谛...",
            "characters": [
                {"name": "古董店老板", "avatar": "/placeholder.svg?height=60&width=60", "description": "收藏各种古董的神秘老人"},
                {"name": "音乐学生", "avatar": "/placeholder.svg?height=60&width=60", "description": "学习音乐的年轻女孩"},
                {"name": "退休教师", "avatar": "/placeholder.svg?height=60&width=60", "description": "充满智慧的退休老教师"},
                {"name": "小男孩", "avatar": "/placeholder.svg?height=60&width=60", "description": "对音乐盒着迷的天真孩子"},
            ]
        }
    ]

    # 将所有剧本数据插入数据库
    for script_data in scripts_data:
        script = Script(
            id=script_data["id"],
            title=script_data["title"],
            cover=script_data["cover"],
            category=script_data["category"],
            tags=script_data["tags"],
            players=script_data["players"],
            difficulty=script_data["difficulty"],
            duration=script_data["duration"],
            author=script_data["author"],
            description=script_data["description"],
            characters=script_data["characters"]
        )
        db.add(script)

    db.commit()  # 提交事务，保存到数据库
    print(f"成功创建了 {len(scripts_data)} 个剧本的初始数据。")
else:
    print("数据已存在，跳过初始化。")

# 关闭数据库会话
db.close()

if __name__ == "__main__":
    print("数据库和表格创建完成。初始化数据脚本执行结束。")