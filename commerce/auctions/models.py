from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from datetime import datetime, date
import math


def time_since_creation(date_created):
    now = datetime.now(date_created.tzinfo)
    delta = now - date_created
    seconds = delta.total_seconds()
    if seconds < 60:
        seconds = math.floor(seconds)
        seconds = 1 if seconds == 0 else seconds
        return f"{seconds:.0f} s ago"
    minutes = seconds / 60
    if minutes < 60:
        minutes = math.floor(minutes)
        return f"{minutes:.0f} m ago"
    hours = minutes / 60
    if hours < 24:
        hours = math.floor(hours)
        return f"{hours:.0f} h ago"
    return date_created.strftime("%d/%m/%Y")


class User(AbstractUser):
    watchlist = models.ManyToManyField('Auction', blank=True, related_name='watched_by')

    @classmethod
    def winning_auctions(cls, user):
        user_bids = Bid.objects.filter(user=user).order_by('auction')
        winning_auctions = []
        for bid in user_bids:
            if bid.auction in winning_auctions:
                continue
            if user == Bid.current_bid_user(auction=bid.auction):
                winning_auctions.append(bid.auction)
            else:
                winning_auctions.append(bid.auction)
        return winning_auctions
    

class Category(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name

    @property
    def number_auctions(self):
        auctions = self.auctions.all()
        return len(auctions)


class Auction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='auctions')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)
    minimum_bid = models.FloatField()
    date_created = models.DateTimeField(auto_now_add=True)
    image_url = models.URLField(null=True, blank=True, max_length=500)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='auctions')
    closed = models.BooleanField(default=False)
    bid_minimum_increase = models.FloatField(default=5)
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        category = self.category if self.category is not None else "No Category"
        return f"{self.name} ({category})"

    @property
    def current_bid(self):
        bid_values = list(self.bids.all().values_list('value', flat=True))
        if bid_values:
            return max(bid_values)
        else:
            return 0
        
    @property
    def time_since_creation(self):
       return time_since_creation(self.date_created)
        
    @property
    def min_next_bid(self):
        if self.current_bid < self.minimum_bid:
            return self.minimum_bid
        else:
            return self.current_bid + self.bid_minimum_increase

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        text_begin = self.text[:17] + "..." if len(self.text) > 20 else self.text 
        return f"{self.auction} comment - {self.user}: {text_begin}"

    def clean(self):
        if len(self.text) == 0:
            raise ValidationError("Empty comments cannot be posted.")
        
    @property
    def time_since_creation(self):
        return time_since_creation(self.date_created)


class Bid(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bids")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    date_created = models.DateTimeField(auto_now_add=True)
    value = models.FloatField()

    def __str__(self):
        return f"{self.auction} bid - {self.user}: {self.value:.2f}"

    def clean(self):
        if self.value <= 0:
            raise ValidationError("Bid value must be bigger than 0.")
        elif self.value < self.auction.minimum_bid:
            raise ValidationError(f"Bid value must be bigger than {self.auction} action minimum bid ({self.auction.minimum_bid:.2f}).")
        
    @classmethod
    def current_bid_user(self, auction):
        highest_bid = Bid.objects.filter(auction=auction).aggregate(max_value=models.Max('value'))
        if not highest_bid:
            raise Exception(f"No bi found for {auction.name}.")
        bid_with_highest_value = Bid.objects.filter(auction=auction, value=highest_bid['max_value']).first()
        return bid_with_highest_value.user
        