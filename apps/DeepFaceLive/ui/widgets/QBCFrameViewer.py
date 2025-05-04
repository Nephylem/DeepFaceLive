from localization import L
from resources.fonts import QXFontDB
from xlib import qt as qtx

from ... import backend


class QBCFrameViewer(qtx.QXCollapsibleSection):
    """
    A collapsible widget that displays video frames from a backend connection.
    Inherits from QXCollapsibleSection to provide expandable/collapsible behavior.
    """

    def __init__(
        self,
        backed_weak_heap: backend.BackendWeakHeap,
        bc: backend.BackendConnection,
        preview_width=256,
    ):
        # Initialize timer that triggers frame updates every 16ms (approx. 60 FPS)
        self._timer = qtx.QXTimer(interval=16, timeout=self._on_timer_16ms, start=True)

        # Store reference to weak heap for memory management
        self._backed_weak_heap = backed_weak_heap
        # Store backend connection for receiving frames
        self._bc = bc
        # Track the current frame ID
        self._bcd_id = None

        # Create image display widget with fixed dimensions
        layered_images = self._layered_images = qtx.QXFixedLayeredImages(
            preview_width, preview_width
        )
        # Create label for displaying frame information
        info_label = self._info_label = qtx.QXLabel(
            font=QXFontDB.get_fixedwidth_font(size=7)
        )

        # Create vertical layout containing image viewer and info label
        main_l = qtx.QXVBoxLayout(
            [
                (layered_images, qtx.AlignCenter),
                (info_label, qtx.AlignCenter),
            ]
        )
        # Initialize parent class with title and layout
        super().__init__(title=L("@QBCFrameViewer.title"), content_layout=main_l)

    def _on_timer_16ms(self):
        """
        Timer callback that updates the frame display every 16ms
        """
        # Check if window is visible and not minimized
        top_qx = self.get_top_QXWindow()
        if not self.is_opened() or (top_qx is not None and top_qx.is_minimized()):
            return

        # Get latest frame ID from backend
        bcd_id = self._bc.get_write_id()
        if self._bcd_id != bcd_id:
            # If new frame available, update current frame ID and get frame data
            bcd, self._bcd_id = self._bc.get_by_id(bcd_id), bcd_id

            if bcd is not None:
                # Associate frame data with weak heap for memory management
                bcd.assign_weak_heap(self._backed_weak_heap)

                # Clear previous frame
                self._layered_images.clear_images()

                # Get new frame image name and data
                frame_image_name = bcd.get_frame_image_name()
                frame_image = bcd.get_image(frame_image_name)

                if frame_image is not None:
                    # Display new frame and update info label with dimensions
                    self._layered_images.add_image(frame_image)
                    h, w = frame_image.shape[:2]
                    self._info_label.setText(f"{frame_image_name} {w}x{h}")

    def clear(self):
        """
        Clear all displayed images from the viewer
        """
        self._layered_images.clear_images()
