package main

import (
	"encoding/json"
	"fmt"
	"net/url"
	"strconv"
	"strings"

	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	focusedStyle        = lipgloss.NewStyle().Foreground(lipgloss.Color("205"))
	blurredStyle        = lipgloss.NewStyle().Foreground(lipgloss.Color("240"))
	cursorStyle         = focusedStyle.Copy()
	noStyle             = lipgloss.NewStyle()
	helpStyleForm       = blurredStyle.Copy()
	cursorModeHelpStyle = lipgloss.NewStyle().Foreground(lipgloss.Color("244"))

	focusedButton = focusedStyle.Copy().Render("[ Submit ]")
	blurredButton = fmt.Sprintf("[ %s ]", blurredStyle.Render("Submit"))
)

type formModel struct {
	focusIndex int
	inputs     []textinput.Model
	cursorMode textinput.CursorMode
	submitted  bool
	values     []string
	title      string
}

func initialFormModel(title string, fields []string, isPassword []bool) formModel {
	m := formModel{
		inputs: make([]textinput.Model, len(fields)),
		title:  title,
	}

	var t textinput.Model
	for i := range fields {
		t = textinput.New()
		t.Cursor.Style = cursorStyle
		t.CharLimit = 156

		if isPassword[i] {
			t.EchoMode = textinput.EchoPassword
			t.EchoCharacter = '•'
		}

		t.Placeholder = fields[i]
		t.PromptStyle = focusedStyle
		t.TextStyle = focusedStyle

		if i == 0 {
			t.Focus()
		}

		m.inputs[i] = t
	}

	return m
}

func (m formModel) Init() tea.Cmd {
	return textinput.Blink
}

func (m formModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c", "esc":
			return m, tea.Quit

		case "tab", "shift+tab", "enter", "up", "down":
			s := msg.String()

			if s == "enter" && m.focusIndex == len(m.inputs) {
				m.submitted = true
				m.values = make([]string, len(m.inputs))
				for i, input := range m.inputs {
					m.values[i] = input.Value()
				}
				return m, tea.Quit
			}

			if s == "up" || s == "shift+tab" {
				m.focusIndex--
			} else {
				m.focusIndex++
			}

			if m.focusIndex > len(m.inputs) {
				m.focusIndex = 0
			} else if m.focusIndex < 0 {
				m.focusIndex = len(m.inputs)
			}

			cmds := make([]tea.Cmd, len(m.inputs))
			for i := 0; i <= len(m.inputs)-1; i++ {
				if i == m.focusIndex {
					cmds[i] = m.inputs[i].Focus()
					m.inputs[i].PromptStyle = focusedStyle
					m.inputs[i].TextStyle = focusedStyle
					continue
				}
				m.inputs[i].Blur()
				m.inputs[i].PromptStyle = noStyle
				m.inputs[i].TextStyle = noStyle
			}

			return m, tea.Batch(cmds...)
		}
	}

	cmd := m.updateInputs(msg)
	return m, cmd
}

func (m *formModel) updateInputs(msg tea.Msg) tea.Cmd {
	cmds := make([]tea.Cmd, len(m.inputs))

	for i := range m.inputs {
		m.inputs[i], cmds[i] = m.inputs[i].Update(msg)
	}

	return tea.Batch(cmds...)
}

func (m formModel) View() string {
	if m.submitted {
		return ""
	}

	var b strings.Builder

	b.WriteString(lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("205")).Render(m.title))
	b.WriteString("\n\n")

	for i := range m.inputs {
		b.WriteString(m.inputs[i].View())
		if i < len(m.inputs)-1 {
			b.WriteRune('\n')
		}
	}

	button := &blurredButton
	if m.focusIndex == len(m.inputs) {
		button = &focusedButton
	}
	fmt.Fprintf(&b, "\n\n%s\n\n", *button)

	b.WriteString(helpStyleForm.Render("cursor: blink"))
	b.WriteString(helpStyleForm.Render(" • tab/shift+tab: navigate • enter: submit • esc: cancel"))

	return b.String()
}

func runForm(title string, fields []string, isPassword []bool) ([]string, bool) {
	m := initialFormModel(title, fields, isPassword)
	p := tea.NewProgram(m)

	model, err := p.Run()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return nil, false
	}

	if m, ok := model.(formModel); ok {
		return m.values, m.submitted
	}

	return nil, false
}

func CreateAccountInteractive() {
	values, submitted := runForm(
		"Create New Account",
		[]string{"Name", "Username", "Password"},
		[]bool{false, false, true},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := RegisterRequest{
		Name:     strings.TrimSpace(values[0]),
		Username: strings.TrimSpace(values[1]),
		Password: strings.TrimSpace(values[2]),
	}

	resp, err := sendPostRequest("/account/register", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result RegisterResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ Registered with buyer ID: %d\n", result.BuyerID)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func LoginInteractive() {
	values, submitted := runForm(
		"Login",
		[]string{"Username", "Password"},
		[]bool{false, true},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := LoginRequest{
		Username: strings.TrimSpace(values[0]),
		Password: strings.TrimSpace(values[1]),
	}

	resp, err := sendPostRequest("/account/login", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result LoginResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		if result.SessionID != 0 {
			SessionId = result.SessionID
			fmt.Printf("\n✓ Logged in with Session ID: %d\n", SessionId)
		}
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func LogoutInteractive() {
	req := LogoutRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/account/logout", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		SessionId = 0
		fmt.Println("\n✓ Session cleared.")
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func GetCategoriesInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/categories", params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result CategoriesResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Printf("\n✗ %s\n", result.Message)
		return
	}

	fmt.Println("\n" + lipgloss.NewStyle().Bold(true).Render("Categories"))
	fmt.Println(strings.Repeat("─", 50))

	for _, c := range result.Categories {
		fmt.Printf("[%d] %s\n", c.ID, c.Name)
	}
}

func SearchItemsInteractive() {
	values, submitted := runForm(
		"Search Items",
		[]string{"Category ID (0 for all)", "Keywords (comma-separated, optional)"},
		[]bool{false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))
	params.Add("category", strings.TrimSpace(values[0]))
	if strings.TrimSpace(values[1]) != "" {
		params.Add("keywords", strings.TrimSpace(values[1]))
	}

	resp, err := sendGetRequest("/items/search", params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result ItemsResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Printf("\n✗ %s\n", result.Message)
		return
	}

	fmt.Println("\n" + lipgloss.NewStyle().Bold(true).Render("Search Results"))
	fmt.Println(strings.Repeat("─", 50))

	printItems(result.Items)
}

func GetItemInteractive() {
	values, submitted := runForm(
		"Get Item Details",
		[]string{"Item ID"},
		[]bool{false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	endpoint := fmt.Sprintf("/items/%s", strings.TrimSpace(values[0]))
	resp, err := sendGetRequest(endpoint, params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result ItemResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Println()
		printItem(result.Item)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func AddToCartInteractive() {
	values, submitted := runForm(
		"Add to Cart",
		[]string{"Item ID", "Quantity"},
		[]bool{false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := CartItemRequest{
		ItemID:    strings.TrimSpace(values[0]),
		Quantity:  strings.TrimSpace(values[1]),
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/items", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func RemoveFromCartInteractive() {
	values, submitted := runForm(
		"Remove from Cart",
		[]string{"Item ID"},
		[]bool{false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := RemoveCartItemRequest{
		SessionID: SessionId,
		ItemID:    strings.TrimSpace(values[0]),
	}

	endpoint := fmt.Sprintf("/cart/items/%s", strings.TrimSpace(values[0]))
	resp, err := sendDeleteRequest(endpoint, req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func DisplayCartInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/cart", params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result CartResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Printf("\n✗ %s\n", result.Message)
		return
	}

	fmt.Println("\n" + lipgloss.NewStyle().Bold(true).Render("Shopping Cart"))
	fmt.Println(strings.Repeat("═", 50))

	if len(result.SessionCart) > 0 {
		fmt.Println("\nSession Cart:")
		for _, item := range result.SessionCart {
			fmt.Printf("  Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
		}
	} else {
		fmt.Println("\nSession Cart: Empty")
	}

	if len(result.SavedCart) > 0 {
		fmt.Println("\nSaved Cart:")
		for _, item := range result.SavedCart {
			fmt.Printf("  Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
		}
	}
}

func SaveCartInteractive() {
	req := SessionRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/save", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func ClearCartInteractive() {
	req := SessionRequest{
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/cart/clear", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func MakePurchaseInteractive() {
	values, submitted := runForm(
		"Complete Purchase",
		[]string{"Card Number", "Expiration Date (MM/YY)", "Security Code (CVV)"},
		[]bool{false, false, true},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := MakePurchaseRequest{
		SessionID:      SessionId,
		CardNumber:     strings.TrimSpace(values[0]),
		ExpirationDate: strings.TrimSpace(values[1]),
		SecurityCode:   strings.TrimSpace(values[2]),
	}

	resp, err := sendPostRequest("/purchase", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func ViewPurchaseHistoryInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/purchases", params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result PurchasesResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Printf("\n✗ %s\n", result.Message)
		return
	}

	if len(result.Purchases) == 0 {
		fmt.Println("\nNo purchases found")
		return
	}

	fmt.Println("\n" + lipgloss.NewStyle().Bold(true).Render("Purchase History"))
	fmt.Println(strings.Repeat("─", 50))
	for _, item := range result.Purchases {
		fmt.Printf("Item ID: %d, Quantity: %d\n", item.ItemID, item.Quantity)
	}
}

func ProvideFeedbackInteractive() {
	values, submitted := runForm(
		"Provide Feedback",
		[]string{"Item ID", "Feedback (up/down)"},
		[]bool{false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	feedback := strings.ToLower(strings.TrimSpace(values[1]))

	if feedback != "up" && feedback != "down" {
		fmt.Println("\n✗ Invalid feedback. Please enter 'up' or 'down'.")
		return
	}

	feedbackValue := "1"
	if feedback == "down" {
		feedbackValue = "-1"
	}

	req := FeedbackRequest{
		ItemID:    strings.TrimSpace(values[0]),
		Feedback:  feedbackValue,
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/feedback", req)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result BaseResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ %s\n", result.Message)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func GetSellerRatingInteractive() {
	values, submitted := runForm(
		"Get Seller Rating",
		[]string{"Seller ID"},
		[]bool{false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	endpoint := fmt.Sprintf("/seller/%s/rating", strings.TrimSpace(values[0]))
	resp, err := sendGetRequest(endpoint, params)
	if err != nil {
		fmt.Printf("\n✗ Error: %v\n", err)
		return
	}

	var result SellerRatingResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		sign := ""
		if result.Feedback > 0 {
			sign = "+"
		}
		fmt.Printf("\n✓ Seller rating: %s%d\n", sign, int(result.Feedback))
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}
