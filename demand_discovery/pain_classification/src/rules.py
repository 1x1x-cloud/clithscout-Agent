"""ClothScout module; migrated without changing business thresholds."""


RULES = [
    ("too_long", r"\btoo long\b|\blegs? (?:are|is) (?:way |much )?too long\b|裤腿太长|裤子太长", "评价者认为衣物过长", "目标衣长/裤内长、所购尺码及成衣实测"),
    ("too_short", r"\btoo short\b|裤腿太短|衣服太短", "评价者认为衣物过短", "目标衣长/裤内长、所购尺码及成衣实测"),
    ("too_big", r"\btoo (?:big|large|loose)\b|\bruns? (?:big|large)\b|太大|偏大", "评价者认为衣物偏大", "偏大部位、所购尺码、目标尺寸和原商品尺寸"),
    ("too_small", r"\btoo (?:small|tight)\b|\bruns? small\b|太小|偏小|太紧", "评价者认为衣物偏小或过紧", "偏小部位、所购尺码、目标尺寸和原商品尺寸"),
    ("fit_unspecified", r"\bdoes(?:n['’]t| not) fit\b|\b(?:didn['’]t|did not) fit\b|\bbarely fit\b|不合身", "评价者表示不合身但方向未明确", "偏差方向、部位、所购尺码和目标尺寸"),
    ("drape", r"\bnot as flowy\b|\bnot flowy\b|\bdoes(?:n['’]t| not) drape\b|不垂坠", "评价者认为垂坠或飘逸表现不足", "可接受的垂坠表现及样衣对照；不能推定成分"),
    ("transparency", r"\bsee[- ]through\b|\btoo sheer\b|透底|太透", "评价者提到透视/遮蔽不足", "穿着光线、颜色、拉伸条件及实物遮蔽测试"),
    ("shrinkage", r"\b(?:shrank|shrunk)\b|缩水", "评价者报告缩水", "洗护条件、洗前洗后实测及可接受偏差"),
    ("seam_failure", r"\bseams? (?:ripped|split|came apart)\b|\bstitching (?:came|fell) (?:apart|out)\b|开线", "评价者报告缝线/接缝问题", "故障位置、使用条件与实物检验"),
    ("material_feel", r"\b(?:fabric|material) (?:feels? |is )?cheap\b|\bcheap (?:fabric|material)\b|\bitchy\b|面料廉价|扎皮肤", "评价者对面料触感不满", "可接受的触感和实物对照；必须材质仍未知"),
]


ISSUES = {key: {"statement": statement, "unknown": unknown} for key, _, statement, unknown in RULES}
