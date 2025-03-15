import discord
import random
import datetime
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

admin_id = #your id
TOKEN = "" #your bot token
@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다!')
    try:
        synced = await bot.tree.sync()
        print(f"슬래시 명령어가 동기화되었습니다: {synced}")
    except Exception as e:
        print(e)

user_balances = {}
user_last_reward_date = {}

ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

class BlackjackGame:
    def __init__(self, soft_17_rule="H17"):
        self.player_hand = []
        self.dealer_hand = []
        self.cards = [{'rank': rank} for rank in ranks] * 4
        self.soft_17_rule = soft_17_rule

    def reset_deck(self):
        self.cards = [{'rank': rank} for rank in ranks] * 4
        random.shuffle(self.cards)

    def deal_cards(self):
        if len(self.cards) < 4:
            self.reset_deck()
        else:
            random.shuffle(self.cards)
        self.player_hand = [self.cards.pop(), self.cards.pop()]
        self.dealer_hand = [self.cards.pop(), self.cards.pop()]

    def hit(self, hand):
        if not self.cards:
            self.reset_deck()
        hand.append(self.cards.pop())

    def reveal_dealer_card(self):
        return self.dealer_hand[0]

    def calculate_total(self, hand):
        total = 0
        aces = 0
        for card in hand:
            if card["rank"] in ['J', 'Q', 'K']:
                total += 10
            elif card["rank"] == 'A':
                aces += 1
            else:
                total += int(card["rank"])
        for _ in range(aces):
            if total + 11 <= 21:
                total += 11
            else:
                total += 1
        return total

    def is_blackjack(self, hand):
        return len(hand) == 2 and self.calculate_total(hand) == 21

    def is_soft_17(self, hand):
        total = 0
        aces = 0
        for card in hand:
            if card["rank"] in ['J', 'Q', 'K']:
                total += 10
            elif card["rank"] == 'A':
                aces += 1
            else:
                total += int(card["rank"])
        return aces > 0 and total + 11 == 17

@bot.tree.command(name='블랙잭', description='블랙잭 게임을 시작합니다.')
@app_commands.describe(bet_amount="베팅할 금액을 입력하세요.")
async def start_blackjack(interaction: discord.Interaction, bet_amount: int):
    if bet_amount <= 0:
        await interaction.response.send_message(embed=discord.Embed(title="오류", description="베팅 금액은 0보다 커야 합니다.", color=discord.Color.red()))
        return

    if interaction.user.id not in user_balances:
        user_balances[interaction.user.id] = 0

    if user_balances[interaction.user.id] < bet_amount:
        await interaction.response.send_message(embed=discord.Embed(title="오류", description="잔액이 부족합니다.", color=discord.Color.red()))
        return

    game = BlackjackGame(soft_17_rule="H17")
    game.deal_cards()

    dealer_card = game.reveal_dealer_card()
    embed = discord.Embed(title="블랙잭", description=f'딜러의 첫 번째 카드: {dealer_card["rank"]}', color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

    player_cards_str = ', '.join([card["rank"] for card in game.player_hand])
    player_total = game.calculate_total(game.player_hand)
    embed = discord.Embed(title="블랙잭", description=f'플레이어의 카드: {player_cards_str}\n합계: {player_total}\n히트 하려면 `h`, 스테이 하려면 `s`를 입력해주세요.', color=discord.Color.green())
    await interaction.channel.send(embed=embed)

    if game.is_blackjack(game.player_hand):
        dealer_total = game.calculate_total(game.dealer_hand)
        dealer_cards_str = ', '.join([card["rank"] for card in game.dealer_hand])
        embed = discord.Embed(title="블랙잭", description=f'딜러의 카드: {dealer_cards_str}\n합계: {dealer_total}', color=discord.Color.blue())
        await interaction.channel.send(embed=embed)

        if game.is_blackjack(game.dealer_hand):
            embed = discord.Embed(title="블랙잭", description="플레이어와 딜러 모두 블랙잭! 무승부입니다.", color=discord.Color.yellow())
            await interaction.channel.send(embed=embed)
        else:
            winnings = int(bet_amount * 2)
            user_balances[interaction.user.id] += winnings + bet_amount
            embed = discord.Embed(title="블랙잭", description=f"블랙잭! {winnings}원을 획득했습니다.\n현재 잔액: {user_balances[interaction.user.id]}원", color=discord.Color.green())
            await interaction.channel.send(embed=embed)
        return

    while True:
        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel and msg.content.lower() in ['h', 's']

        try:
            choice_msg = await bot.wait_for('message', check=check, timeout=60)
            choice = choice_msg.content.lower()

            if choice == 'h':
                game.hit(game.player_hand)
                player_cards_str = ', '.join([card["rank"] for card in game.player_hand])
                player_total = game.calculate_total(game.player_hand)
                embed = discord.Embed(title="블랙잭", description=f'히트를 선택하셨습니다.\n플레이어의 카드: {player_cards_str}\n합계: {player_total}', color=discord.Color.green())
                await interaction.channel.send(embed=embed)

                if player_total > 21:
                    embed = discord.Embed(title="블랙잭", description='플레이어가 버스트되었습니다.', color=discord.Color.red())
                    await interaction.channel.send(embed=embed)
                    user_balances[interaction.user.id] -= bet_amount
                    return
            else:
                break
        except TimeoutError:
            embed = discord.Embed(title="블랙잭", description='시간이 초과되었습니다.', color=discord.Color.red())
            await interaction.channel.send(embed=embed)
            user_balances[interaction.user.id] -= bet_amount
            return

    dealer_cards_str = ', '.join([card["rank"] for card in game.dealer_hand])
    dealer_total = game.calculate_total(game.dealer_hand)
    embed = discord.Embed(title="블랙잭", description=f'딜러의 카드: {dealer_cards_str}\n합계: {dealer_total}', color=discord.Color.blue())
    await interaction.channel.send(embed=embed)

    while dealer_total < 17 or (game.soft_17_rule == "H17" and dealer_total == 17 and game.is_soft_17(game.dealer_hand)):
        game.hit(game.dealer_hand)
        dealer_total = game.calculate_total(game.dealer_hand)
        dealer_cards_str = ', '.join([card["rank"] for card in game.dealer_hand])
        embed = discord.Embed(title="블랙잭", description=f'딜러가 카드를 뽑았습니다.\n딜러의 카드: {dealer_cards_str}\n합계: {dealer_total}', color=discord.Color.blue())
        await interaction.channel.send(embed=embed)

    if dealer_total > 21:
        embed = discord.Embed(title="블랙잭", description='딜러가 버스트되었습니다.', color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        user_balances[interaction.user.id] += bet_amount * 2
    elif dealer_total > player_total:
        embed = discord.Embed(title="블랙잭", description='딜러가 이겼습니다.', color=discord.Color.red())
        await interaction.channel.send(embed=embed)
        user_balances[interaction.user.id] -= bet_amount
    elif dealer_total < player_total:
        embed = discord.Embed(title="블랙잭", description='플레이어가 이겼습니다.', color=discord.Color.green())
        await interaction.channel.send(embed=embed)
        user_balances[interaction.user.id] += bet_amount * 2
    else:
        embed = discord.Embed(title="블랙잭", description='무승부입니다.', color=discord.Color.yellow())
        await interaction.channel.send(embed=embed)

@bot.tree.command(name='무료돈', description='하루에 한 번 무료 돈을 받습니다.')
async def free_money(interaction: discord.Interaction):
    today = datetime.date.today()
    user_id = interaction.user.id

    if user_id not in user_balances:
        user_balances[user_id] = 0

    if user_id in user_last_reward_date and user_last_reward_date[user_id] == today:
        embed = discord.Embed(title="오류", description="오늘은 이미 무료 돈을 받으셨습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    reward = 1000
    user_balances[user_id] += reward
    user_last_reward_date[user_id] = today

    embed = discord.Embed(title="무료돈", description=f"{reward}원을 받으셨습니다!\n현재 잔액: {user_balances[user_id]}원", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='돈주기', description='관리자가 유저에게 돈을 줍니다.')
@app_commands.describe(target="돈을 줄 유저를 선택하세요.", amount="줄 금액을 입력하세요.")
async def give_money(interaction: discord.Interaction, target: discord.User, amount: int):
    if interaction.user.id != admin_id:
        embed = discord.Embed(title="오류", description="이 명령어는 관리자만 사용할 수 있습니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    if amount <= 0:
        embed = discord.Embed(title="오류", description="금액은 0보다 커야 합니다.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    if target.id not in user_balances:
        user_balances[target.id] = 0

    user_balances[target.id] += amount

    embed = discord.Embed(
        title="돈 지급 완료",
        description=f"{target.mention}님에게 {amount}원을 지급했습니다.\n현재 잔액: {user_balances[target.id]}원",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='잔액확인', description='본인의 현재 잔액을 확인합니다.')
async def check_balance(interaction: discord.Interaction):
    user_id = interaction.user.id

    if user_id not in user_balances:
        user_balances[user_id] = 0

    embed = discord.Embed(
        title="잔액 확인",
        description=f"{interaction.user.mention}님의 현재 잔액: {user_balances[user_id]}원",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
