"""Stop words for keyword extraction. Kept short and readable on purpose."""

ENGLISH = set(
    """
a about above after again against all also am an and any are aren't as at be because been before being
below between both but by can can't cannot could couldn't did didn't do does doesn't doing don't down
during each even ever every few for from further get gets getting got had hadn't has hasn't have haven't
having he her here hers herself him himself his how however i i'm i've if in into is isn't it it's its
itself just let's like made make makes many may me might more most much must my myself new no nor not
now of off on once one only or other our ours ourselves out over own really said same say says see she
should shouldn't since so some still such than that that's the their theirs them themselves then there
there's these they they're this those though through to too under until up upon us use used using very
via want was wasn't way we we're were weren't what what's when where which while who whom why will with
without won't would wouldn't yeah yes yet you you're your yours yourself yourselves
amp com http https www html quot gt lt nbsp rt
going know think thing things people time year years day days back first last good bad well
lot right sure actually probably maybe something anything nothing someone anyone everyone
two three four five per around today week month news report reports according
""".split()
)

ARABIC = set(
    """
في من على الى إلى عن مع هذا هذه ذلك تلك التي الذي الذين هو هي هم هن انا نحن انت انتم كان كانت يكون
تكون قد لقد لا لم لن ما ماذا متى اين كيف كل بعض غير بين بعد قبل عند حتى او أو ثم لكن بل اذا إذا ان أن
إن كما ايضا أيضا وقد وفي ومن وعلى وهو وهي فى الي علي عليه عليها فيه فيها منه منها به بها له لها لهم
خلال حيث حول ضد دون منذ امام أمام اكثر أكثر اقل أقل جدا يوم اليوم عام العام قال وقال قالت اليوم
""".split()
)
