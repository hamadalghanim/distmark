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
		return
	}

	var result RegisterResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ Registered with seller ID: %d\n", result.SellerID)
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

func GetSellerRatingInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/seller/rating", params)
	if err != nil {
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

func RegisterItemForSaleInteractive() {
	values, submitted := runForm(
		"Register New Item",
		[]string{"Item Name", "Category ID", "Price", "Quantity"},
		[]bool{false, false, false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := RegisterItemRequest{
		Name:      strings.TrimSpace(values[0]),
		Category:  strings.TrimSpace(values[1]),
		Price:     strings.TrimSpace(values[2]),
		Qty:       strings.TrimSpace(values[3]),
		SessionID: SessionId,
	}

	resp, err := sendPostRequest("/items", req)
	if err != nil {
		return
	}

	var result RegisterItemResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ Item registered with ID: %d\n", result.ItemID)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func ChangeItemPriceInteractive() {
	values, submitted := runForm(
		"Change Item Price",
		[]string{"Item ID", "New Price"},
		[]bool{false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := ChangePriceRequest{
		ItemID:    strings.TrimSpace(values[0]),
		NewPrice:  strings.TrimSpace(values[1]),
		SessionID: SessionId,
	}

	resp, err := sendPutRequest("/items/price", req)
	if err != nil {
		return
	}

	var result ChangePriceResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ Price updated to $%.2f\n", result.CurrentPrice)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func UpdateUnitsForSaleInteractive() {
	values, submitted := runForm(
		"Update Item Quantity",
		[]string{"Item ID", "New Quantity"},
		[]bool{false, false},
	)

	if !submitted {
		fmt.Println("Cancelled.")
		return
	}

	req := ChangeQuantityRequest{
		ItemID:    strings.TrimSpace(values[0]),
		NewQty:    strings.TrimSpace(values[1]),
		SessionID: SessionId,
	}

	resp, err := sendPutRequest("/items/quantity", req)
	if err != nil {
		return
	}

	var result ChangeQuantityResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result == "success" {
		fmt.Printf("\n✓ Quantity updated to %d\n", result.CurrentQuantity)
	} else {
		fmt.Printf("\n✗ %s\n", result.Message)
	}
}

func DisplayItemsForSaleInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/items", params)
	if err != nil {
		return
	}

	var result ItemsResponse
	json.Unmarshal([]byte(resp), &result)

	if result.Result != "success" {
		fmt.Printf("\n✗ %s\n", result.Message)
		return
	}

	fmt.Println("\n" + lipgloss.NewStyle().Bold(true).Render("Items For Sale"))
	fmt.Println(strings.Repeat("─", 70))

	printItems(result.Items)
}

func GetCategoriesInteractive() {
	params := url.Values{}
	params.Add("session_id", strconv.Itoa(SessionId))

	resp, err := sendGetRequest("/categories", params)
	if err != nil {
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
