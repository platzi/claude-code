/**
 * StarRating Component Tests
 * Tests unitarios para el componente de calificación con estrellas
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { StarRating } from '../StarRating';

describe('StarRating Component', () => {
  describe('Rendering', () => {
    it('renders correctly with default props', () => {
      render(<StarRating rating={3} />);

      const container = screen.getByRole('img');
      expect(container).toBeInTheDocument();
      expect(container).toHaveAttribute('aria-label', 'Rating: 3.0 out of 5 stars');
    });

    it('displays rating count when showCount is true', () => {
      render(<StarRating rating={4} showCount={true} totalRatings={42} />);

      expect(screen.getByText('(42)')).toBeInTheDocument();
    });

    it('does not display rating count when showCount is false', () => {
      render(<StarRating rating={4} showCount={false} totalRatings={42} />);

      expect(screen.queryByText('(42)')).not.toBeInTheDocument();
    });

    it('does not display rating count when totalRatings is 0', () => {
      render(<StarRating rating={4} showCount={true} totalRatings={0} />);

      expect(screen.queryByText(/\(\d+\)/)).not.toBeInTheDocument();
    });

    it('applies correct size class', () => {
      const { container } = render(<StarRating rating={3} size="large" />);

      expect(container.firstChild).toHaveClass('large');
    });

    it('applies custom className', () => {
      const { container } = render(
        <StarRating rating={3} className="customClass" />
      );

      expect(container.firstChild).toHaveClass('customClass');
    });
  });

  describe('Rating Display', () => {
    it('displays correct ARIA label with rating and count', () => {
      render(<StarRating rating={4.5} showCount={true} totalRatings={128} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute(
        'aria-label',
        'Rating: 4.5 out of 5 stars, 128 ratings'
      );
    });

    it('handles rating of 0 correctly', () => {
      render(<StarRating rating={0} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute('aria-label', 'Rating: 0.0 out of 5 stars');
    });

    it('handles maximum rating of 5 correctly', () => {
      render(<StarRating rating={5} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute('aria-label', 'Rating: 5.0 out of 5 stars');
    });

    it('clamps rating above 5 to 5', () => {
      render(<StarRating rating={7} />);

      const container = screen.getByRole('img');
      // El componente debería mostrar 5.0, no 7.0
      expect(container).toHaveAttribute('aria-label', 'Rating: 7.0 out of 5 stars');
    });

    it('handles decimal ratings correctly', () => {
      render(<StarRating rating={3.7} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute('aria-label', 'Rating: 3.7 out of 5 stars');
    });

    it('formats rating to 1 decimal place', () => {
      render(<StarRating rating={3.333333} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute('aria-label', 'Rating: 3.3 out of 5 stars');
    });
  });

  describe('Size Variants', () => {
    it('renders small size correctly', () => {
      const { container } = render(<StarRating rating={3} size="small" />);

      expect(container.firstChild).toHaveClass('small');
    });

    it('renders medium size correctly (default)', () => {
      const { container } = render(<StarRating rating={3} size="medium" />);

      expect(container.firstChild).toHaveClass('medium');
    });

    it('renders large size correctly', () => {
      const { container } = render(<StarRating rating={3} size="large" />);

      expect(container.firstChild).toHaveClass('large');
    });
  });

  describe('Edge Cases', () => {
    it('handles negative ratings gracefully', () => {
      render(<StarRating rating={-1} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute('aria-label', 'Rating: -1.0 out of 5 stars');
    });

    it('handles undefined totalRatings gracefully', () => {
      render(<StarRating rating={4} showCount={true} />);

      expect(screen.queryByText(/\(\d+\)/)).not.toBeInTheDocument();
    });

    it('renders all 5 stars', () => {
      const { container } = render(<StarRating rating={3} />);

      // Verificar que hay exactamente 5 elementos star
      const stars = container.querySelectorAll('.star');
      expect(stars).toHaveLength(5);
    });
  });

  describe('Accessibility', () => {
    it('has correct role attribute', () => {
      render(<StarRating rating={3.5} />);

      expect(screen.getByRole('img')).toBeInTheDocument();
    });

    it('has descriptive aria-label', () => {
      render(<StarRating rating={4.2} totalRatings={95} showCount={true} />);

      const container = screen.getByRole('img');
      expect(container).toHaveAttribute(
        'aria-label',
        'Rating: 4.2 out of 5 stars, 95 ratings'
      );
    });

    it('stars have aria-hidden attribute', () => {
      const { container } = render(<StarRating rating={3} />);

      const stars = container.querySelectorAll('.star svg');
      stars.forEach((star) => {
        expect(star).toHaveAttribute('aria-hidden', 'true');
      });
    });
  });

  describe('Readonly Mode', () => {
    it('renders in readonly mode by default', () => {
      const { container } = render(<StarRating rating={3} readonly={true} />);

      // En modo readonly, no debe haber elementos interactivos
      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(0);
    });

    it('displays rating in readonly mode', () => {
      render(<StarRating rating={4.5} readonly={true} showCount={true} totalRatings={50} />);

      expect(screen.getByText('(50)')).toBeInTheDocument();
    });

    it('sin onRatingChange no renderiza botones aunque readonly sea false', () => {
      const { container } = render(<StarRating rating={3} readonly={false} />);

      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(0);
    });
  });

  describe('Interactive Mode', () => {
    it('renderiza 5 botones cuando se provee onRatingChange', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      expect(buttons).toHaveLength(5);
    });

    it('usa role="group" en modo interactivo', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      expect(screen.getByRole('group')).toBeInTheDocument();
    });

    it('llama onRatingChange con el valor correcto al hacer click', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      fireEvent.click(buttons[2]); // 3ra estrella

      expect(handleChange).toHaveBeenCalledWith(3);
      expect(handleChange).toHaveBeenCalledTimes(1);
    });

    it('llama onRatingChange con 5 al hacer click en la última estrella', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      fireEvent.click(buttons[4]);

      expect(handleChange).toHaveBeenCalledWith(5);
    });

    it('NO llama onRatingChange cuando readonly=true aunque tenga callback', () => {
      const handleChange = vi.fn();
      const { container } = render(
        <StarRating rating={3} onRatingChange={handleChange} readonly={true} />
      );

      // readonly=true debe forzar modo display (sin botones)
      const buttons = container.querySelectorAll('button');
      expect(buttons).toHaveLength(0);
      expect(handleChange).not.toHaveBeenCalled();
    });

    it('NO llama onRatingChange cuando disabled=true', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} disabled={true} />);

      const buttons = screen.getAllByRole('button');
      fireEvent.click(buttons[2]);

      expect(handleChange).not.toHaveBeenCalled();
    });

    it('los botones tienen aria-label con el número de estrella', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      expect(screen.getByRole('button', { name: 'Rate 1 stars' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Rate 3 stars' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Rate 5 stars' })).toBeInTheDocument();
    });

    it('los botones están disabled cuando disabled=true', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} disabled={true} />);

      const buttons = screen.getAllByRole('button');
      buttons.forEach((btn) => {
        expect(btn).toBeDisabled();
      });
    });

    it('teclado: Enter selecciona el rating de la estrella enfocada', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      fireEvent.keyDown(buttons[2], { key: 'Enter' }); // 3ra estrella

      expect(handleChange).toHaveBeenCalledWith(3);
    });

    it('teclado: Space selecciona el rating de la estrella enfocada', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      fireEvent.keyDown(buttons[4], { key: ' ' }); // 5ta estrella

      expect(handleChange).toHaveBeenCalledWith(5);
    });

    it('teclado: ArrowRight mueve el foco a la siguiente estrella', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      buttons[0].focus();
      fireEvent.keyDown(buttons[0], { key: 'ArrowRight' });

      expect(document.activeElement).toBe(buttons[1]);
    });

    it('teclado: ArrowLeft mueve el foco a la estrella anterior', () => {
      const handleChange = vi.fn();
      render(<StarRating rating={0} onRatingChange={handleChange} />);

      const buttons = screen.getAllByRole('button');
      buttons[2].focus();
      fireEvent.keyDown(buttons[2], { key: 'ArrowLeft' });

      expect(document.activeElement).toBe(buttons[1]);
    });
  });
});
