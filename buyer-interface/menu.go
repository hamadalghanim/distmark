package main

import (
	"fmt"
	"io"
	"strings"

	"github.com/charmbracelet/bubbles/list"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"
)

var (
	titleStyle        = lipgloss.NewStyle().MarginLeft(2).Bold(true).Foreground(lipgloss.Color("205"))
	itemStyle         = lipgloss.NewStyle().PaddingLeft(4)
	selectedItemStyle = lipgloss.NewStyle().PaddingLeft(2).Foreground(lipgloss.Color("170")).Bold(true)
	paginationStyle   = list.DefaultStyles().PaginationStyle.PaddingLeft(4)
	helpStyle         = list.DefaultStyles().HelpStyle.PaddingLeft(4).PaddingBottom(1)
	quitTextStyle     = lipgloss.NewStyle().Margin(1, 0, 2, 4)
)

type menuItem struct {
	title       string
	description string
	action      string
}

func (i menuItem) FilterValue() string { return i.title }

type menuItemDelegate struct{}

func (d menuItemDelegate) Height() int                             { return 1 }
func (d menuItemDelegate) Spacing() int                            { return 0 }
func (d menuItemDelegate) Update(_ tea.Msg, _ *list.Model) tea.Cmd { return nil }
func (d menuItemDelegate) Render(w io.Writer, m list.Model, index int, listItem list.Item) {
	i, ok := listItem.(menuItem)
	if !ok {
		return
	}

	str := fmt.Sprintf("%d. %s", index+1, i.title)

	fn := itemStyle.Render
	if index == m.Index() {
		fn = func(s ...string) string {
			return selectedItemStyle.Render("→ " + strings.Join(s, " "))
		}
	}

	fmt.Fprint(w, fn(str))
}

type menuModel struct {
	list         list.Model
	choice       string
	quitting     bool
	sessionID    int
	showLoggedIn bool
}

func initialMenuModel() menuModel {
	items := []list.Item{
		menuItem{title: "Create Account", description: "Register a new buyer account", action: "createaccount"},
		menuItem{title: "Login", description: "Login with username and password", action: "login"},
		menuItem{title: "Logout", description: "End active session", action: "logout"},
		menuItem{title: "Get Categories", description: "List all available categories", action: "categories"},
		menuItem{title: "Search Items", description: "Search for items by category/keywords", action: "search"},
		menuItem{title: "Get Item Details", description: "View details of a specific item", action: "getitem"},
		menuItem{title: "Add to Cart", description: "Add item to shopping cart", action: "addcart"},
		menuItem{title: "Remove from Cart", description: "Remove item from cart", action: "removecart"},
		menuItem{title: "Display Cart", description: "View shopping cart contents", action: "viewcart"},
		menuItem{title: "Save Cart", description: "Save cart for later", action: "savecart"},
		menuItem{title: "Clear Cart", description: "Empty shopping cart", action: "clearcart"},
		menuItem{title: "Make Purchase", description: "Complete purchase with payment", action: "purchase"},
		menuItem{title: "View Purchase History", description: "See past purchases", action: "history"},
		menuItem{title: "Provide Feedback", description: "Rate a seller", action: "feedback"},
		menuItem{title: "Get Seller Rating", description: "View seller's rating", action: "rating"},
		menuItem{title: "Exit", description: "Quit the application", action: "exit"},
	}

	const defaultWidth = 80
	const listHeight = 18

	l := list.New(items, menuItemDelegate{}, defaultWidth, listHeight)
	l.Title = "Buyer Shopping System"
	l.SetShowStatusBar(false)
	l.SetFilteringEnabled(false)
	l.Styles.Title = titleStyle
	l.Styles.PaginationStyle = paginationStyle
	l.Styles.HelpStyle = helpStyle

	return menuModel{list: l}
}

func (m menuModel) Init() tea.Cmd {
	return nil
}

func (m menuModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.WindowSizeMsg:
		m.list.SetWidth(msg.Width)
		return m, nil

	case tea.KeyMsg:
		switch keypress := msg.String(); keypress {
		case "ctrl+c":
			m.quitting = true
			return m, tea.Quit

		case "enter":
			i, ok := m.list.SelectedItem().(menuItem)
			if ok {
				m.choice = i.action
			}
			return m, tea.Quit
		}
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m menuModel) View() string {
	if m.choice != "" {
		return ""
	}
	if m.quitting {
		return quitTextStyle.Render("Goodbye!\n")
	}

	header := ""
	if SessionId != 0 {
		header = lipgloss.NewStyle().
			Foreground(lipgloss.Color("42")).
			Bold(true).
			MarginLeft(2).
			MarginBottom(1).
			Render(fmt.Sprintf("● Logged in (Session ID: %d)", SessionId))
		header += "\n"
	}

	return header + "\n" + m.list.View()
}

func ShowInteractiveMenu() string {
	m := initialMenuModel()
	p := tea.NewProgram(m)

	if model, err := p.Run(); err != nil {
		fmt.Println("Error running menu:", err)
		return ""
	} else {
		if m, ok := model.(menuModel); ok {
			return m.choice
		}
	}
	return ""
}
