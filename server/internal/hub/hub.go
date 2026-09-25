package hub

import "context"

type UserName = string

type Update map[UserName]float64

type Hub struct {
	Updates     chan Update
	Subscribe   chan chan Update
	Unsubscribe chan chan Update
}

func NewHub() *Hub {
	return &Hub{
		Updates:     make(chan Update),
		Subscribe:   make(chan chan Update),
		Unsubscribe: make(chan chan Update),
	}
}

func (h *Hub) Run(ctx context.Context) {
	subscribers := make(map[chan Update]struct{})

	for {
		select {
		case <-ctx.Done():
			return
		case ch := <-h.Subscribe:
			subscribers[ch] = struct{}{}
		case ch := <-h.Unsubscribe:
			delete(subscribers, ch)
			close(ch)
		case update := <-h.Updates:
			for ch := range subscribers {
				select {
				case ch <- update:
				default:
					// subscriber isn't keeping up
				}
			}
		}
	}

}
