package main

import (
	"fmt"
	"strings"
)

type CartItem struct {
	ItemID   int
	Quantity int
}

type Cart map[int]CartItem

func (cart Cart) AddToCart(itemID int, quantity int) {
	if existingItem, exists := cart[itemID]; exists {
		existingItem.Quantity += quantity
		cart[itemID] = existingItem
	} else {
		cart[itemID] = CartItem{
			ItemID:   itemID,
			Quantity: quantity,
		}
	}
}

func (cart Cart) RemoveFromCart(itemID int, quantity int) {
	if existingItem, exists := cart[itemID]; exists {
		if existingItem.Quantity <= quantity {
			delete(cart, itemID)
		} else {
			existingItem.Quantity -= quantity
			cart[itemID] = existingItem
		}
	}
}

func (cart *Cart) ClearCart() {
	*cart = make(map[int]CartItem)
}

func (cart Cart) buildCartItemsString() string {
	var items []string
	for _, item := range cart {
		items = append(items, fmt.Sprintf("%d:%d", item.ItemID, item.Quantity))
	}
	return strings.Join(items, ",")
}
